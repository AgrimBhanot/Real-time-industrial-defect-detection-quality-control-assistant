from __future__ import annotations

import json
import logging
import queue
import threading
import time
from typing import Callable, Optional

from qc.advisory.llm import TemplateLLM, build_llm
from qc.advisory.validator import extract_json, repair_json, validate
from qc.config import Config
from qc.schema import AdviceResult, InspectionRecord

log = logging.getLogger(__name__)


class Advisor:
    """record -> validated advice. Retries the LLM, then falls back to the SOP template (flagged as fallback)."""

    def __init__(self, cfg: Config):
        a = cfg.section("advisory")
        self.profile = cfg.profile
        self.template = TemplateLLM(cfg.profile)
        self.primary = build_llm(cfg)
        self.retries = int(a.get("retries", 1))

    @property
    def backend(self) -> str:
        return self.primary.name

    def start(self) -> None:
        """Load the LLM before the first unit arrives (persistent server). Failures fall back per call."""
        start = getattr(self.primary, "start", None)
        if start:
            try:
                info = start()
                log.info("advisory backend %s ready: %s", self.primary.name, info)
            except Exception as exc:
                log.error("advisory backend %s failed to start: %s (template fallback per unit)",
                          self.primary.name, exc)

    def close(self) -> None:
        close = getattr(self.primary, "close", None)
        if close:
            close()

    def advise(self, record: InspectionRecord) -> AdviceResult:
        if isinstance(self.primary, TemplateLLM):
            out = self.template.advise(record)
            advice, errors = validate(out.text, record, self.profile)
            return AdviceResult(record.unit_id, advice or {}, "template", valid=advice is not None,
                                fallback=False, errors=errors, total_ms=out.stats.get("total_ms"), raw=out.text)
        errors, stats, raw, attempts = [], {}, "", 0
        for _ in range(1 + self.retries):
            attempts += 1
            try:
                out = self.primary.advise(record)
            except Exception as exc:  # runner crash / timeout must never stop the line
                errors.append(f"attempt {attempts}: {exc}")
                continue
            stats, raw = out.stats, out.text
            notes: list = []
            advice, errs = validate(out.text, record, self.profile, notes)
            if advice is None and errs == ["missing key 'log_entry'"]:
                # Llama gave summary/causes/actions/verify but skipped the log line: build that one field from the
                # record (deterministic) and validate again; counted as repaired, never as a clean answer.
                obj = extract_json(out.text) or repair_json(out.text)[0] or {}
                obj["log_entry"] = json.loads(self.template.advise(record).text)["log_entry"]
                advice, errs = validate(json.dumps(obj), record, self.profile)
                notes.append("log_entry built from the record")
            if advice:
                res = self._result(record, advice, self.primary.name, True, False, attempts, errors, stats, raw)
                res.repaired = bool(notes)
                if notes:
                    res.errors = errors + [f"attempt {attempts}: repaired: {'; '.join(notes)}"]
                return res
            errors += [f"attempt {attempts}: {e}" for e in errs]
        fb = self.template.advise(record)
        advice, _ = validate(fb.text, record, self.profile)
        return self._result(record, advice or {}, "template", False, True, attempts, errors, stats, raw)

    @staticmethod
    def _result(record, advice, backend, valid, fallback, attempts, errors, stats, raw) -> AdviceResult:
        return AdviceResult(
            record.unit_id, advice, backend, valid=valid, fallback=fallback, attempts=attempts, errors=errors,
            ttft_ms=stats.get("ttft_ms"), tok_s=stats.get("tok_s"),
            total_ms=stats.get("total_ms") or stats.get("wall_ms"), load_ms=stats.get("load_ms"),
            prompt_tokens=stats.get("prompt_tokens"), generated_tokens=stats.get("generated_tokens"), raw=raw,
            loop_stop=bool(stats.get("loop_stop")),
        )


class AdvisoryWorker(threading.Thread):
    """Runs advice off the inspection loop. When the queue is full the oldest pending unit is dropped."""

    def __init__(self, advisor: Advisor, on_result: Optional[Callable[[AdviceResult], None]] = None,
                 maxsize: int = 8):
        super().__init__(daemon=True, name="advisory")
        self.advisor, self.on_result = advisor, on_result
        self.q: queue.Queue = queue.Queue(maxsize=maxsize)
        self.dropped = 0
        self._halt = threading.Event()  # not "_stop": that name shadows a Thread internal used by join()

    def submit(self, record: InspectionRecord, t_captured: Optional[float] = None) -> None:
        """t_captured: time.perf_counter() when the frame was grabbed, for frame -> advice latency."""
        item = (record, time.perf_counter(), t_captured)
        while True:
            try:
                self.q.put_nowait(item)
                return
            except queue.Full:
                try:
                    self.q.get_nowait()
                    self.q.task_done()
                    self.dropped += 1
                except queue.Empty:
                    pass

    def stop(self) -> None:
        self._halt.set()

    @property
    def idle(self) -> bool:
        return self.q.unfinished_tasks == 0

    def run(self) -> None:
        self.advisor.start()
        while not self._halt.is_set():
            try:
                record, t_submit, t_captured = self.q.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                t_start = time.perf_counter()
                result = self.advisor.advise(record)
                t_done = time.perf_counter()
                result.queue_ms = (t_start - t_submit) * 1000
                if t_captured is not None:
                    result.e2e_ms = (t_done - t_captured) * 1000
                if self.on_result:
                    self.on_result(result)
            except Exception:
                log.exception("advisory failed for %s", record.unit_id)
            finally:
                self.q.task_done()
