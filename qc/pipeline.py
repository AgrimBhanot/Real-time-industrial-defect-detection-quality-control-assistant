"""Inspection loop: source -> detector -> rule engine -> log -> (async) advisory -> UI state.

Two kinds of line share this loop. On a conveyor of images every frame is a unit. On a live camera the view is analysed
continuously, and a unit is logged when the trigger says the parts are at rest (or the operator asks for one).
"""
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
from qc.sources import CameraSource, Frame, PartsTrigger, build_source
from qc.storage import InspectionDB
from qc.telemetry import Telemetry
from qc.vision import build_detector
from qc.vision.detector import read_yolo_labels

log = logging.getLogger(__name__)


class SharedState:
    def __init__(self, keep_advice: int = 200, keep_units: int = 48):
        self.lock = threading.Lock()
        self.jpeg: Optional[bytes] = None          # newest view with overlay
        self.record: Optional[dict] = None         # last logged unit
        self.live: Optional[dict] = None           # what the camera sees right now (not logged)
        self.advice: dict = {}
        self.advice_order: deque = deque(maxlen=keep_advice)
        self.recent: deque = deque(maxlen=keep_units)   # film strip: [{unit_id, result, gt_outcome}]
        self.fps = 0.0
        self.source_error: Optional[str] = None
        self.error: Optional[str] = None           # why the inspection loop stopped
        self.counts: Counter = Counter()
        self.gt_counts: Counter = Counter()

    def set_frame(self, jpeg: bytes, record: InspectionRecord, fps: float) -> None:
        with self.lock:
            self.jpeg, self.record, self.fps = jpeg, record.to_dict(), fps
            self.count(record)

    def count(self, record: InspectionRecord) -> None:
        self.counts[record.inspection_result] += 1
        if record.gt_outcome:
            self.gt_counts[record.gt_outcome] += 1
        self.recent.append({"unit_id": record.unit_id, "result": record.inspection_result,
                            "gt_outcome": record.gt_outcome, "n_defects": len(record.detections)})

    def set_live(self, jpeg: bytes, record: InspectionRecord, fps: float) -> None:
        with self.lock:
            self.jpeg, self.fps = jpeg, fps
            self.live = {"result": record.inspection_result, "parts": record.part_counts,
                         "defects": len(record.detections), "vision_ms": record.timings_ms.get("vision")}

    def set_unit(self, record: InspectionRecord) -> None:
        with self.lock:
            self.record = record.to_dict()
            self.count(record)

    def set_advice(self, r: AdviceResult) -> None:
        with self.lock:
            if len(self.advice_order) == self.advice_order.maxlen:
                self.advice.pop(self.advice_order[0], None)
            self.advice_order.append(r.unit_id)
            self.advice[r.unit_id] = r.to_dict()


class Control:
    """Operator controls: pause/play, single step, conveyor pace, inspect now."""

    def __init__(self, fps_limit: float = 0.0):
        self.fps_limit = fps_limit
        self._run = threading.Event()
        self._run.set()
        self._step = threading.Semaphore(0)
        self._inspect = threading.Event()

    @property
    def paused(self) -> bool:
        return not self._run.is_set()

    def pause(self) -> None:
        self._run.clear()

    def play(self) -> None:
        self._run.set()

    def step(self) -> None:
        self._run.clear()
        self._step.release()

    def inspect_now(self) -> None:
        self._inspect.set()

    def take_inspect(self) -> bool:
        hit = self._inspect.is_set()
        self._inspect.clear()
        return hit

    def wait_turn(self, halted) -> None:
        """Block a paused conveyor until play, a step, or shutdown."""
        while self.paused and not halted():
            if self._step.acquire(timeout=0.1):
                return


class Pipeline:
    def __init__(self, cfg: Config, with_advisory: Optional[bool] = None, with_telemetry: bool = True,
                 db: Optional[InspectionDB] = None, llm_server=None):
        """db / llm_server: shared by several lines (qc/app/line.py); otherwise the pipeline owns its own."""
        self.cfg = cfg
        lg = cfg.section("logging")
        self.profile_name = cfg.profile_name
        self.source = build_source(cfg)
        self.inspect = bool(cfg.section("source").get("inspect", True))  # false: show the camera, inspect nothing
        self.keep_alive = False  # serve(): keep retrying a missing camera instead of ending the run
        self.detector = build_detector(cfg) if self.inspect else None
        self.rules = RuleEngine(cfg.profile)
        self.db = db or InspectionDB(cfg.path(lg.get("db", "runs/inspections.db")))
        self.save_frames = lg.get("save_frames", "defective")
        self.frames_dir = cfg.path(lg.get("frames_dir", "runs/frames"))
        self.history: deque = deque(maxlen=int(lg.get("context_window", 50)))
        self.state = SharedState()
        self.run_id = datetime.now().strftime("%m%d-%H%M%S")
        self.n = 0
        self.control = Control(float(cfg.section("source").get("fps_limit", 0) or 0))
        cam = cfg.section("source").get("camera", {})
        self.trigger = None
        if isinstance(self.source, CameraSource) and cam.get("trigger") == "parts":
            p = {k: v for k, v in (cam.get("trigger_params") or {}).items() if k in ("still_px", "moved_px", "still_frac", "change_frac", "diff")}
            self.trigger = PartsTrigger(frames=int(cam.get("parts_frames", 8)), **p)

        adv = cfg.section("advisory")
        enabled = adv.get("enabled", True) if with_advisory is None else with_advisory
        self.submit_when = set(adv.get("submit_when", ["FAIL", "REVIEW", "PASS_WITH_NOTE"]))
        self.worker: Optional[AdvisoryWorker] = None
        if enabled and self.inspect:
            self.advisor = Advisor(cfg, llm_server)
            self.worker = AdvisoryWorker(self.advisor, self._on_advice, maxsize=int(adv.get("queue_size", 8)),
                                         prioritise=bool(adv.get("prioritise", False)))
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

    def analyse(self, frame: Frame) -> InspectionRecord:
        """Detect and decide; nothing is logged."""
        h, w = frame.image.shape[:2]
        t0 = time.perf_counter()
        dets, vt = self.detector.detect(frame)
        t1 = time.perf_counter()
        trace = self.rules.annotate(dets, w, h)
        result, decision = self.rules.decide(dets)
        t2 = time.perf_counter()
        rec = InspectionRecord(
            unit_id="", timestamp=datetime.now().astimezone().isoformat(timespec="milliseconds"),
            source=frame.source, image_ref=frame.ref, image_size=[w, h], detections=dets,
            inspection_result=result, rule_trace=trace + decision, context=self._context(),
            timings_ms={**vt, "vision": (t1 - t0) * 1000, "rules": (t2 - t1) * 1000}, parts=frame.parts,
        )
        if frame.label_path and getattr(self.detector, "backend", "") != "groundtruth":
            gts = read_yolo_labels(frame.label_path, w, h, self.cfg.profile["classes"])
            self.rules.annotate(gts, w, h)
            rec.gt_result = self.rules.decide(gts)[0] if gts else "PASS"
            rec.gt_defects = sorted(d.defect for d in gts)
        return rec

    def commit(self, rec: InspectionRecord, frame: Frame) -> InspectionRecord:
        """Give the unit its id, log it and queue it for advice."""
        self.n += 1
        rec.unit_id = f"U-{self.run_id}-{self.n:05d}"
        self.history.append((rec.inspection_result, rec.defect_classes))
        frame_path = None
        if self.save_frames == "all" or (self.save_frames == "defective" and rec.detections):
            self.frames_dir.mkdir(parents=True, exist_ok=True)
            frame_path = str(self.frames_dir / f"{rec.unit_id}.jpg")
            cv2.imwrite(frame_path, frame.image)
        rec.timings_ms["e2e"] = (time.perf_counter() - frame.t_captured) * 1000
        self.db.log_inspection(rec, self.profile_name, frame_path, session=self.run_id)
        if self.worker and rec.detections and rec.inspection_result in self.submit_when:
            self.worker.submit(rec, frame.t_captured)
        return rec

    def process(self, frame: Frame) -> InspectionRecord:
        return self.commit(self.analyse(frame), frame)

    def _frames(self):
        while True:
            try:
                for frame in self.source:
                    self.state.source_error = None
                    yield frame
                return
            except RuntimeError as exc:
                if not (self.keep_alive and isinstance(self.source, CameraSource)):
                    raise
                if self.state.source_error is None:
                    log.warning("%s; retrying every 3 s", exc)
                self.state.source_error = str(exc)
                if self._halt.wait(3):
                    return

    def _preview(self) -> None:
        last, fps = time.perf_counter(), 0.0
        for _ in self._frames():
            if self._halt.is_set():
                return
            now = time.perf_counter()
            fps = 0.9 * fps + 0.1 / max(now - last, 1e-6) if fps else 1 / max(now - last, 1e-6)
            last, self.state.fps = now, fps

    def run(self, max_frames: Optional[int] = None, on_record=None, render: bool = True) -> None:
        """max_frames counts logged units."""
        if self.worker:
            self.worker.start()
        if self.telemetry and self.telemetry.available:
            self.telemetry.start()
        try:
            if not self.inspect:
                self._preview()
                return
            self.detector.warmup()
            self._loop(max_frames, on_record, render)
        except Exception as exc:
            self.state.error = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            self.shutdown()

    def _loop(self, max_frames, on_record, render) -> None:
        fps_ema, last, last_metrics, done = 0.0, time.perf_counter(), 0.0, 0
        live = self.trigger is not None
        halted = self._halt.is_set
        frames = iter(self._frames())
        while not halted() and (max_frames is None or done < max_frames):
            if not live:
                self.control.wait_turn(halted)
                if halted():
                    break
            frame = next(frames, None)
            if frame is None:
                break
            rec = self.analyse(frame)
            if live:
                at_rest = self.trigger.update(frame.parts, frame.image)
                unit = self.control.take_inspect() or (at_rest and not self.control.paused)
            else:
                unit = True
            if unit:
                self.commit(rec, frame)
                done += 1
            now = time.perf_counter()
            dt = now - last
            min_dt = 1.0 / self.control.fps_limit if self.control.fps_limit > 0 and not live else 0.0
            if min_dt and dt < min_dt:
                self._halt.wait(min_dt - dt)
                now = time.perf_counter()
                dt = now - last
            last = now
            fps_ema = (1 / dt) if fps_ema == 0 else 0.9 * fps_ema + 0.1 * (1 / dt)
            if render:
                ok, jpg = cv2.imencode(".jpg", overlay.draw(frame.image, rec, fps_ema if live else None, live=live,
                                                          max_width=1280),
                                       [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ok and live:
                    self.state.set_live(jpg.tobytes(), rec, fps_ema)
                elif ok:
                    self.state.set_frame(jpg.tobytes(), rec, fps_ema)
            if unit and live:
                self.state.set_unit(rec)
            if self.telemetry and now - last_metrics > 5:
                self.db.log_metrics(self.telemetry.snapshot())
                last_metrics = now
            if unit and on_record:
                on_record(rec)

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
        """Stop the advisory worker and, unless it is shared, the Llama server process."""
        if self.worker:
            self.worker.stop()
            self.advisor.close()
