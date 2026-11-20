"""Advisory runtime (runtime B): Llama 3.2 via the ExecuTorch runner on the Arm CPU, plus a deterministic template."""
from __future__ import annotations

import json
import queue
import re
import subprocess
import threading
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from qc.advisory.prompt import build_messages, llama3_chat
from qc.config import Config
from qc.schema import InspectionRecord

ASSISTANT_MARKER = "assistant<|end_header_id|>"


@dataclass
class LLMOutput:
    text: str
    stats: dict = field(default_factory=dict)


class TemplateLLM:
    """Deterministic SOP-based advice. Primary backend before Llama is ready, fallback after."""
    name = "template"

    def __init__(self, profile: dict):
        self.profile = profile

    def advise(self, record: InspectionRecord) -> LLMOutput:
        t0 = time.perf_counter()
        sop = self.profile.get("sop", {})
        dets = sorted(record.detections, key=lambda d: ("low", "medium", "high").index(d.severity or "low"),
                      reverse=True)
        top = dets[0]
        counts = Counter(d.defect for d in dets)
        what = ", ".join(f"{n}x {c}" for c, n in counts.most_common())
        causes, actions = [], []
        for c in counts:
            causes += sop.get(c, {}).get("causes", [])[:2]
            actions += sop.get(c, {}).get("actions", [])[:2]
        recent = record.context.get("recent_defects", {}).get(top.defect, 0)
        repeat = f"; {recent} {top.defect} in last {record.context.get('recent_units', 0)} units" if recent else ""
        advice = {
            "summary": f"{record.inspection_result.replace('_', ' ')}: {what}; worst is {top.severity} "
                       f"{top.defect} in zone {top.zone}.",
            "likely_causes": list(dict.fromkeys(causes))[:3] or ["not in SOP table"],
            "recommended_actions": list(dict.fromkeys(actions))[:3] or ["escalate to process engineer"],
            "verify": f"Re-inspect the next 5 units for {top.defect}.",
            "log_entry": f"{record.unit_id} {record.inspection_result} {top.defect}/{top.severity} {top.zone}{repeat}.",
        }
        return LLMOutput(json.dumps(advice), {"total_ms": (time.perf_counter() - t0) * 1000})


def parse_observer(text: str) -> dict:
    """Timing stats from the 'PyTorchObserver {...}' line the ExecuTorch llama runner prints."""
    m = None
    for m in re.finditer(r"PyTorchObserver\s*(\{.*\})", text):
        pass
    if not m:
        return {}
    try:
        d = json.loads(m.group(1))
    except json.JSONDecodeError:
        return {}
    return stats_from_runner(d)


def stats_from_runner(d: dict) -> dict:
    """ExecuTorch llm::Stats JSON (absolute ms timestamps) -> TTFT, decode tok/s, totals."""
    scale = float(d.get("SCALING_FACTOR_UNITS_PER_SECOND", 1000))

    def ms(a: str, b: str):
        return (d[b] - d[a]) * 1000.0 / scale if a in d and b in d else None

    load = ms("model_load_start_ms", "model_load_end_ms")
    out = {
        "load_ms": load if load else None,  # 0 when the model was already loaded (persistent server)
        "ttft_ms": ms("inference_start_ms", "first_token_ms"),
        "total_ms": ms("inference_start_ms", "inference_end_ms"),
        "prompt_tokens": d.get("prompt_tokens"),
        "generated_tokens": d.get("generated_tokens"),
    }
    decode_ms = ms("first_token_ms", "inference_end_ms")
    gen = d.get("generated_tokens") or 0
    out["tok_s"] = (gen - 1) / (decode_ms / 1000.0) if decode_ms and gen > 1 else None
    return out


def _clean(text: str) -> str:
    for tok in ("<|eot_id|>", "<|end_of_text|>"):
        text = text.replace(tok, "")
    return text.strip()


class LLMServerClient:
    """Talks to native/qc_llm_server (one persistent OS process, model loaded once). See its header for the
    length-prefixed protocol. A reader thread parses replies so every call can time out cleanly."""

    def __init__(self, argv: list[str], log_path: Path, start_timeout: float, call_timeout: float):
        self.argv, self.log_path = argv, log_path
        self.start_timeout, self.call_timeout = start_timeout, call_timeout
        self.proc: Optional[subprocess.Popen] = None
        self.replies: queue.Queue = queue.Queue()
        self.info: dict = {}

    @property
    def pid(self) -> Optional[int]:
        return self.proc.pid if self.proc and self.proc.poll() is None else None

    def _reader(self, proc: subprocess.Popen, replies: queue.Queue) -> None:
        out = proc.stdout
        try:
            while True:
                line = out.readline()
                if not line:
                    break
                head, _, rest = line.decode("utf-8", "replace").rstrip("\n").partition(" ")
                if head == "READY":
                    replies.put(("READY", json.loads(rest or "{}")))
                elif head == "OK":
                    text = out.read(int(rest)).decode("utf-8", "replace")
                    stats_line = out.readline().decode("utf-8", "replace")
                    stats = json.loads(stats_line.partition(" ")[2] or "{}")
                    replies.put(("OK", (text, stats)))
                else:  # ERR / FATAL / unexpected
                    replies.put((head, rest))
        except Exception as exc:  # malformed reply: surface it to the waiting caller
            replies.put(("ERR", f"reader: {exc}"))
        replies.put(("EXIT", proc.poll()))

    def start(self) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        log = open(self.log_path, "ab")
        self.replies = queue.Queue()
        self.proc = subprocess.Popen(self.argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log)
        threading.Thread(target=self._reader, args=(self.proc, self.replies), daemon=True,
                         name="llm-server-reader").start()
        kind, payload = self._wait(self.start_timeout)
        if kind != "READY":
            self.close()
            raise RuntimeError(f"qc_llm_server failed to start ({kind} {payload}); see {self.log_path}")
        self.info = payload

    def _wait(self, timeout: float):
        try:
            return self.replies.get(timeout=timeout)
        except queue.Empty:
            self.close()
            raise TimeoutError(f"qc_llm_server: no reply within {timeout:.0f}s (process restarted on next call)")

    def generate(self, prompt: str, max_new_tokens: int, temperature: float) -> tuple[str, dict]:
        if self.pid is None:
            self.start()
        data = prompt.encode("utf-8")
        self.proc.stdin.write(f"GEN {int(max_new_tokens)} {float(temperature)} {len(data)}\n".encode() + data)
        self.proc.stdin.flush()
        kind, payload = self._wait(self.call_timeout)
        if kind != "OK":
            if kind == "EXIT":
                self.proc = None
            raise RuntimeError(f"qc_llm_server: {kind} {payload}")
        return payload

    def close(self) -> None:
        p, self.proc = self.proc, None
        if p and p.poll() is None:
            try:
                p.stdin.write(b"QUIT\n")
                p.stdin.flush()
                p.wait(timeout=5)
            except Exception:
                p.kill()


class ExecuTorchLLM:
    """Llama 3.2 1B Instruct (.pte, 8da4w, XNNPACK) through ExecuTorch on the Arm CPU.

    mode=server : persistent qc_llm_server process (default; model loaded once)
    mode=oneshot: ExecuTorch's reference llama_main, one process per call (debugging / gate G1)
    """
    name = "executorch"

    def __init__(self, cfg: Config):
        a = cfg.section("advisory")
        e = a.get("executorch", {})
        self.profile = cfg.profile
        self.mode = e.get("mode", "server")
        self.runner = cfg.path(e["server"] if self.mode == "server" else e["runner"])
        self.model = cfg.path(e["model"])
        self.tokenizer = cfg.path(e["tokenizer"])
        missing = [str(p) for p in (self.runner, self.model, self.tokenizer) if not p.exists()]
        if missing:
            raise FileNotFoundError(
                "ExecuTorch Llama assets missing:\n  " + "\n  ".join(missing) +
                "\n  build the runners: scripts/build_executorch_runner.sh"
                "\n  export the model: scripts/export_llama_pte.sh, then copy to models/llm/"
            )
        self.temperature = float(a.get("temperature", 0.2))
        self.max_new_tokens = int(e.get("max_new_tokens", 200))
        self.timeout = float(e.get("timeout_s", 180))
        self.lock = threading.Lock()  # one generation at a time (advice worker + shift summary share it)
        self.values = {
            "model": str(self.model), "tokenizer": str(self.tokenizer), "temperature": self.temperature,
            "seq_len": e.get("seq_len", 1536), "cpu_threads": e.get("cpu_threads", 4),
        }
        self.arg_templates = e.get("args", [])
        self.server: Optional[LLMServerClient] = None
        if self.mode == "server":
            argv = [str(self.runner), f"--model_path={self.model}", f"--tokenizer_path={self.tokenizer}",
                    f"--cpu_threads={self.values['cpu_threads']}", f"--warmup={str(e.get('warmup', True)).lower()}"]
            self.server = LLMServerClient(argv, cfg.path(e.get("server_log", "runs/logs/llm_server.log")),
                                          start_timeout=float(e.get("start_timeout_s", 120)), call_timeout=self.timeout)

    @property
    def pid(self) -> Optional[int]:
        return self.server.pid if self.server else None

    def start(self) -> dict:
        """Load the model now (otherwise lazily on the first call). Returns load info."""
        with self.lock:
            if self.server and self.server.pid is None:
                self.server.start()
            return dict(self.server.info) if self.server else {}

    def complete(self, prompt: str) -> LLMOutput:
        with self.lock:
            t0 = time.perf_counter()
            if self.server:
                text, raw_stats = self.server.generate(prompt, self.max_new_tokens, self.temperature)
                stats = stats_from_runner(raw_stats)
                stats["loop_stop"] = raw_stats.get("loop_stop", 0)
            else:
                text, stats = self._oneshot(prompt)
            stats["wall_ms"] = (time.perf_counter() - t0) * 1000
            return LLMOutput(_clean(text), stats)

    def _oneshot(self, prompt: str) -> tuple[str, dict]:
        args = [str(self.runner)] + [t.format(prompt=prompt, **self.values) for t in self.arg_templates]
        proc = subprocess.run(args, capture_output=True, text=True, timeout=self.timeout)
        if proc.returncode != 0:
            raise RuntimeError(f"llama runner exited {proc.returncode}: {proc.stderr[-600:]}")
        stats = parse_observer(proc.stdout + "\n" + proc.stderr)
        text = proc.stdout
        k = text.rfind(ASSISTANT_MARKER)
        if k >= 0:
            text = text[k + len(ASSISTANT_MARKER):]
        elif prompt in text:
            text = text.split(prompt, 1)[1]
        return re.sub(r"PyTorchObserver\s*\{.*\}", "", text), stats

    def advise(self, record: InspectionRecord) -> LLMOutput:
        return self.complete(llama3_chat(build_messages(record, self.profile)))

    def close(self) -> None:
        if self.server:
            self.server.close()


def build_llm(cfg: Config):
    backend = cfg.section("advisory").get("backend", "template")
    if backend == "template":
        return TemplateLLM(cfg.profile)
    if backend == "executorch":
        return ExecuTorchLLM(cfg)
    raise ValueError(f"unknown advisory.backend {backend!r}")
