"""Teach ExecuTorch's TextLLMRunner (v1.0.0) to reuse the KV cache for the part of a prompt that did not change.

  python native/patch_prefix_cache.py third_party/executorch

Every advice prompt starts with the same system message and worked example. The stock runner recomputes them each time.
This patch keeps the last prompt's tokens, finds how many leading tokens are identical, and prefills only the rest from
that position (positions after it are overwritten). Set QC_NO_PREFIX_CACHE=1 to switch it off for A/B runs.
Running it twice changes nothing; scripts/build_executorch_runner.sh applies it before building.
"""
import sys
from pathlib import Path

MARK = "qc prefix cache"


def edit(path: Path, pairs) -> None:
    s = path.read_text()
    if MARK in s:
        print("already patched:", path)
        return
    for old, new in pairs:
        if s.count(old) != 1:
            sys.exit(f"{path}: expected exactly one match, found {s.count(old)}:\n{old}\n(wrong ExecuTorch version?)")
        s = s.replace(old, new)
    path.write_text(s)
    print("patched:", path)


def main() -> None:
    root = Path(sys.argv[1]) / "extension/llm/runner"
    edit(root / "text_llm_runner.h", [
        ("  int64_t pos_ = 0;\n};",
         f"  int64_t pos_ = 0;\n\n  // {MARK}: tokens whose keys/values are in the cache from position 0\n"
         "  std::vector<uint64_t> cached_tokens_;\n  int64_t reused_tokens_ = 0;\n\n public:\n"
         "  int64_t reused_tokens() const {\n    return reused_tokens_;\n  }\n};"),
    ])
    edit(root / "text_llm_runner.cpp", [
        ("  auto prefill_res = text_prefiller_->prefill(prompt_tokens, pos_);\n"
         "  ET_CHECK_OK_OR_RETURN_ERROR(prefill_res.error());\n",
         f"  // {MARK}: skip the leading tokens that are identical to the previous prompt\n"
         "  reused_tokens_ = 0;\n"
         "  if (pos_ == 0 && std::getenv(\"QC_NO_PREFIX_CACHE\") == nullptr) {\n"
         "    const size_t limit = std::min(cached_tokens_.size(), prompt_tokens.size() - 1);\n"
         "    while (static_cast<size_t>(reused_tokens_) < limit &&\n"
         "           cached_tokens_[reused_tokens_] == prompt_tokens[reused_tokens_]) {\n"
         "      ++reused_tokens_;\n    }\n  }\n"
         "  cached_tokens_.clear(); // until this prefill has succeeded\n"
         "  std::vector<uint64_t> new_tokens(\n"
         "      prompt_tokens.begin() + reused_tokens_, prompt_tokens.end());\n"
         "  int64_t prefill_pos = pos_ + reused_tokens_;\n"
         "  auto prefill_res = text_prefiller_->prefill(new_tokens, prefill_pos);\n"
         "  ET_CHECK_OK_OR_RETURN_ERROR(prefill_res.error());\n"
         "  if (pos_ == 0) {\n    cached_tokens_ = prompt_tokens;\n  }\n  pos_ = prefill_pos;\n"),
    ])
    cpp = root / "text_llm_runner.cpp"
    s = cpp.read_text()
    if "#include <cstdlib>" not in s:
        i = s.index("#include")
        cpp.write_text(s[:i] + "#include <algorithm>\n#include <cstdlib>\n" + s[i:])


if __name__ == "__main__":
    main()
