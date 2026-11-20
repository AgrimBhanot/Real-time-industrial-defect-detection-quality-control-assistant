"""Inspection loop: source -> detector -> rule engine -> log -> (async) advisory -> UI state."""
from __future__ import annotations

import logging
import threading
import time
from collections import Counter, deque
from datetime import datetime
from typing import Optional

import cv2

from qc import overlay
from qc.advisory import Advisor, AdvisoryWorker
from qc.config import Config
from qc.rules import RuleEngine
from qc.schema import AdviceResult, InspectionRecord
from qc.sources import Frame, build_source
from qc.storage import InspectionDB
from qc.telemetry import Telemetry
from qc.vision import build_detector

log = logging.getLogger(__name__)


class SharedState:
    def __init__(self, keep_advice: int = 200):
        self.lock = threading.Lock()
        self.jpeg: Optional[bytes] = None
        self.record: Optional[dict] = None
        self.advice: dict = {}
        self.advice_order: deque = deque(maxlen=keep_advice)
        self.fps = 0.0
        self.counts: Counter = Counter()

    def set_frame(self, jpeg: bytes, record: InspectionRecord, fps: float) -> None:
        with self.lock:
            self.jpeg, self.record, self.fps = jpeg, record.to_dict(), fps
            self.counts[record.inspection_result] += 1

    def set_advice(self, r: AdviceResult) -> None:
        with self.lock:
            if len(self.advice_order) == self.advice_order.maxlen:
                self.advice.pop(self.advice_order[0], None)
            self.advice_order.append(r.unit_id)
            self.advice[r.unit_id] = r.to_dict()


class Pipeline:
    def __init__(self, cfg: Config, with_advisory: Optional[bool] = None, with_telemetry: bool = True):
        self.cfg = cfg
        lg = cfg.section("logging")
        self.profile_name = cfg.profile_name
        self.source = build_source(cfg)
        self.detector = build_detector(cfg)
        self.rules = RuleEngine(cfg.profile)
        self.db = InspectionDB(cfg.path(lg.get("db", "runs/inspections.db")))
        self.save_frames = lg.get("save_frames", "defective")
        self.frames_dir = cfg.path(lg.get("frames_dir", "runs/frames"))
        self.history: deque = deque(maxlen=int(lg.get("context_window", 50)))
        self.state = SharedState()
        self.run_id = datetime.now().strftime("%m%d-%H%M%S")
        self.n = 0
        self.fps_limit = float(cfg.section("source").get("fps_limit", 0) or 0)

        adv = cfg.section("advisory")
        enabled = adv.get("enabled", True) if with_advisory is None else with_advisory
        self.submit_when = set(adv.get("submit_when", ["FAIL", "REVIEW", "PASS_WITH_NOTE"]))
        self.worker: Optional[AdvisoryWorker] = None
        if enabled:
            self.advisor = Advisor(cfg)
            self.worker = AdvisoryWorker(self.advisor, self._on_advice, maxsize=int(adv.get("queue_size", 8)))
        self.telemetry = Telemetry(llm_pid=self._llm_pid) if with_telemetry else None
        self._halt = threading.Event()

    def _llm_pid(self):
        return getattr(self.advisor.primary, "pid", None) if self.worker else None

    def _on_advice(self, r: AdviceResult) -> None:
        self.db.log_advice(r)
        self.state.set_advice(r)

    def _context(self) -> dict:
        defects = Counter(c for _, classes in self.history for c in classes)
        return {
            "station": self.cfg.profile.get("station", ""),
            "recent_units": len(self.history),
            "recent_fail": sum(1 for r, _ in self.history if r == "FAIL"),
            "recent_defects": dict(defects.most_common()),
        }

    def process(self, frame: Frame) -> InspectionRecord:
        self.n += 1
        h, w = frame.image.shape[:2]
        t0 = time.perf_counter()
        dets, vt = self.detector.detect(frame)
        t1 = time.perf_counter()
        trace = self.rules.annotate(dets, w, h)
        result, decision = self.rules.decide(dets)
        t2 = time.perf_counter()
        rec = InspectionRecord(
            unit_id=f"U-{self.run_id}-{self.n:05d}",
            timestamp=datetime.now().astimezone().isoformat(timespec="milliseconds"),
            source=frame.source, image_ref=frame.ref, image_size=[w, h], detections=dets,
            inspection_result=result, rule_trace=trace + decision, context=self._context(),
            timings_ms={**vt, "vision": (t1 - t0) * 1000, "rules": (t2 - t1) * 1000},
        )
        self.history.append((result, rec.defect_classes))

        frame_path = None
        if self.save_frames == "all" or (self.save_frames == "defective" and dets):
            self.frames_dir.mkdir(parents=True, exist_ok=True)
            frame_path = str(self.frames_dir / f"{rec.unit_id}.jpg")
            cv2.imwrite(frame_path, frame.image)
        rec.timings_ms["e2e"] = (time.perf_counter() - frame.t_captured) * 1000
        self.db.log_inspection(rec, self.profile_name, frame_path)
        if self.worker and dets and result in self.submit_when:
            self.worker.submit(rec, frame.t_captured)
        return rec

    def run(self, max_frames: Optional[int] = None, on_record=None, render: bool = True) -> None:
        if self.worker:
            self.worker.start()
        if self.telemetry and self.telemetry.available:
            self.telemetry.start()
        self.detector.warmup()
        fps_ema, last, last_metrics = 0.0, time.perf_counter(), 0.0
        min_dt = 1.0 / self.fps_limit if self.fps_limit > 0 else 0.0
        try:
            for i, frame in enumerate(self.source):
                if self._halt.is_set() or (max_frames is not None and i >= max_frames):
                    break
                rec = self.process(frame)
                now = time.perf_counter()
                dt = now - last
                if min_dt and dt < min_dt:
                    time.sleep(min_dt - dt)
                    now = time.perf_counter()
                    dt = now - last
                last = now
                fps_ema = (1 / dt) if fps_ema == 0 else 0.9 * fps_ema + 0.1 * (1 / dt)
                if render:
                    ok, jpg = cv2.imencode(".jpg", overlay.draw(frame.image, rec, fps_ema),
                                           [cv2.IMWRITE_JPEG_QUALITY, 80])
                    if ok:
                        self.state.set_frame(jpg.tobytes(), rec, fps_ema)
                if self.telemetry and now - last_metrics > 5:
                    self.db.log_metrics(self.telemetry.snapshot())
                    last_metrics = now
                if on_record:
                    on_record(rec)
        finally:
            self.shutdown()

    def drain_advice(self, timeout: float = 600) -> None:
        """Block until queued advice is processed (benchmarks / headless runs)."""
        if not self.worker:
            return
        deadline = time.time() + timeout
        while not self.worker.idle and time.time() < deadline:
            time.sleep(0.2)

    def stop(self) -> None:
        self._halt.set()

    def shutdown(self) -> None:
        if self.telemetry:
            self.telemetry.stop()

    def close(self) -> None:
        """Stop the advisory worker and the Llama server process (call after drain_advice)."""
        if self.worker:
            self.worker.stop()
            self.advisor.close()
