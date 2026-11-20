/*
 * qc_llm_server: persistent ExecuTorch Llama worker for the PS5 QC inspector (runtime B).
 *
 * Loads the .pte once (XNNPACK, Arm CPU), then serves prompts over stdin/stdout so the Python app does
 * not pay the model load for every inspected unit. Built against the same ExecuTorch release as llama_main
 * (scripts/build_executorch_runner.sh) and linked exactly like it.
 *
 * Protocol (length-prefixed, binary safe):
 *   server -> "READY {json}\n"                       after load (+ optional warmup); or "FATAL <msg>\n"
 *   client -> "GEN <max_new_tokens> <temperature> <nbytes>\n" followed by <nbytes> of UTF-8 prompt
 *   server -> "OK <nbytes>\n" <nbytes of generated text> "STATS {json}\n"   or "ERR <code>\n"
 *   client -> "QUIT\n"
 * The runner prints tokens to stdout itself, so the protocol uses a private dup of the original stdout and
 * fd 1 is redirected to stderr.
 */
#include <gflags/gflags.h>
#include <unistd.h>

#include <chrono>
#include <cstdio>
#include <cstring>
#include <optional>
#include <string>

#include <executorch/examples/models/llama/runner/runner.h>
#include <executorch/extension/llm/runner/stats.h>

#if defined(ET_USE_THREADPOOL)
#include <executorch/extension/threadpool/cpuinfo_utils.h>
#include <executorch/extension/threadpool/threadpool.h>
#endif

DEFINE_string(model_path, "", "Llama .pte exported with the same ExecuTorch release.");
DEFINE_string(tokenizer_path, "", "tokenizer.model");
DEFINE_string(data_path, "", "Optional .ptd data file.");
DEFINE_int32(cpu_threads, -1, "Threads for XNNPACK; -1 = number of performant cores.");
DEFINE_bool(warmup, true, "Run one short generation after loading.");
DEFINE_bool(stop_on_loop, true, "Stop generating when the output starts repeating itself.");

namespace llm = ::executorch::extension::llm;
using ::executorch::runtime::Error;

// True when the text ends in three back-to-back copies of a 12-64 char span: a 1B model at low temperature can
// fall into such a loop; stopping early saves seconds and the validator repairs the truncated JSON.
static bool ends_in_loop(const std::string& s) {
  const size_t n = s.size();
  for (size_t p = 12; p <= 64 && 3 * p <= n; ++p) {
    bool repeated = true;
    for (size_t i = n - 2 * p; i < n; ++i) {
      if (s[i] != s[i - p]) {
        repeated = false;
        break;
      }
    }
    if (repeated) {
      return true;
    }
  }
  return false;
}

static long now_ms() {
  return std::chrono::duration_cast<std::chrono::milliseconds>(
             std::chrono::steady_clock::now().time_since_epoch())
      .count();
}

int main(int argc, char** argv) {
  gflags::ParseCommandLineFlags(&argc, &argv, true);

  int proto_fd = dup(STDOUT_FILENO);
  dup2(STDERR_FILENO, STDOUT_FILENO);
  FILE* out = fdopen(proto_fd, "w");
  if (out == nullptr) {
    return 2;
  }

#if defined(ET_USE_THREADPOOL)
  uint32_t threads = FLAGS_cpu_threads == -1
      ? ::executorch::extension::cpuinfo::get_num_performant_cores()
      : static_cast<uint32_t>(FLAGS_cpu_threads);
  if (threads > 0) {
    ::executorch::extension::threadpool::get_threadpool()->_unsafe_reset_threadpool(threads);
  }
#else
  uint32_t threads = 0;
#endif

  long t0 = now_ms();
  const std::optional<const std::string> data_path =
      FLAGS_data_path.empty() ? std::nullopt : std::optional<const std::string>(FLAGS_data_path);
  auto runner = example::create_llama_runner(FLAGS_model_path, FLAGS_tokenizer_path, data_path);
  if (runner == nullptr || runner->load() != Error::Ok) {
    fprintf(out, "FATAL could not load model %s / tokenizer %s\n", FLAGS_model_path.c_str(),
            FLAGS_tokenizer_path.c_str());
    fflush(out);
    return 1;
  }
  long load_ms = now_ms() - t0;
  long warmup_ms = 0;
  if (FLAGS_warmup) {
    long w0 = now_ms();
    runner->warmup("<|begin_of_text|>Hello", 4);
    runner->reset();
    warmup_ms = now_ms() - w0;
  }
  fprintf(out, "READY {\"load_ms\":%ld,\"warmup_ms\":%ld,\"threads\":%u,\"pid\":%d}\n", load_ms, warmup_ms,
          threads, static_cast<int>(getpid()));
  fflush(out);

  char line[256];
  while (fgets(line, sizeof(line), stdin) != nullptr) {
    if (strncmp(line, "QUIT", 4) == 0) {
      break;
    }
    int max_new = 0;
    float temperature = 0.0f;
    size_t nbytes = 0;
    if (sscanf(line, "GEN %d %f %zu", &max_new, &temperature, &nbytes) != 3) {
      fprintf(out, "ERR bad_request\n");
      fflush(out);
      continue;
    }
    std::string prompt(nbytes, '\0');
    if (nbytes > 0 && fread(&prompt[0], 1, nbytes, stdin) != nbytes) {
      break;
    }
    runner->reset();  // fresh KV-cache position: every unit is an independent conversation
    llm::GenerationConfig config;
    config.echo = false;
    config.max_new_tokens = max_new;
    config.temperature = temperature;
    std::string text, stats_json = "{}";
    bool loop_stop = false;
    auto* r = runner.get();
    Error err = runner->generate(
        prompt, config,
        [&text, &loop_stop, r](const std::string& piece) {
          text += piece;
          if (FLAGS_stop_on_loop && !loop_stop && ends_in_loop(text)) {
            loop_stop = true;
            r->stop();
          }
        },
        [&stats_json](const llm::Stats& s) { stats_json = llm::stats_to_json_string(s); });
    if (loop_stop && stats_json.size() > 1) {
      stats_json.insert(1, "\"loop_stop\":1,");
    }
    if (err != Error::Ok) {
      fprintf(out, "ERR %d\n", static_cast<int>(err));
    } else {
      fprintf(out, "OK %zu\n", text.size());
      fwrite(text.data(), 1, text.size(), out);
      fprintf(out, "STATS %s\n", stats_json.c_str());
    }
    fflush(out);
  }
  return 0;
}
