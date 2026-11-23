"""Vision pipeline (runtime A). One interface, several backends:

  tensorrt     best.engine via Ultralytics -> TensorRT on the Orin GPU
  onnxruntime  best.onnx   via Ultralytics -> ONNX Runtime (CUDA/TensorRT EP if onnxruntime-gpu is installed)
  torch        best.pt     via Ultralytics -> PyTorch CUDA
  groundtruth  reads YOLO label files next to the images; lets the rest of the system run before a model exists
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

import numpy as np

from qc.config import Config
from qc.schema import Detection
from qc.sources import Frame

WEIGHT_FILES = {"tensorrt": "best.engine", "onnxruntime": "best.onnx", "torch": "best.pt"}


def read_yolo_labels(path: str | Path, w: int, h: int, names: list[str]) -> list[Detection]:
    dets = []
    for line in Path(path).read_text().splitlines():
        parts = line.split()
        if len(parts) < 5:
            continue
        cls = int(float(parts[0]))
        cx, cy, bw, bh = (float(v) for v in parts[1:5])
        conf = float(parts[5]) if len(parts) > 5 else 1.0
        x1, y1 = (cx - bw / 2) * w, (cy - bh / 2) * h
        x2, y2 = (cx + bw / 2) * w, (cy + bh / 2) * h
        name = names[cls] if cls < len(names) else f"class{cls}"
        dets.append(Detection(name, conf, [round(x1), round(y1), round(x2), round(y2)]))
    return dets


def check_class_conf(class_conf: Optional[dict], names: list[str]) -> dict[str, float]:
    """Per-class confidence thresholds; a class not listed uses vision.conf."""
    out = {str(k): float(v) for k, v in (class_conf or {}).items()}
    unknown = set(out) - set(names)
    if unknown:
        raise ValueError(f"class_conf names unknown classes: {sorted(unknown)}")
    if any(not 0.0 < v < 1.0 for v in out.values()):
        raise ValueError("class_conf values must be between 0 and 1")
    return out


class GroundTruthDetector:
    backend = "groundtruth"

    def __init__(self, names: list[str]):
        self.names = names

    def warmup(self, n: int = 0) -> None:
        pass

    def detect(self, frame: Frame) -> tuple[list[Detection], dict]:
        t0 = time.perf_counter()
        h, w = frame.image.shape[:2]
        dets = read_yolo_labels(frame.label_path, w, h, self.names) if frame.label_path else []
        return dets, {"pre": 0.0, "infer": (time.perf_counter() - t0) * 1000, "post": 0.0}


class UltralyticsDetector:
    def __init__(self, backend: str, weights: Path, names: list[str], imgsz: int = 640, conf: float = 0.25,
                 iou: float = 0.5, half: bool = True, device: int | str = 0,
                 class_conf: Optional[dict] = None):
        if not weights.exists():
            raise FileNotFoundError(
                f"{backend} weights not found: {weights}\n"
                f"  train on Colab -> copy best.pt here -> python training/export.py --to engine|onnx\n"
                f"  or run with --set vision.backend=groundtruth to exercise the pipeline without a model"
            )
        from ultralytics import YOLO

        self.backend, self.names = backend, names
        self.model = YOLO(str(weights), task="detect")
        self.conf, self.class_conf = conf, check_class_conf(class_conf, names)
        conf = min([conf, *self.class_conf.values()])  # the model must emit everything any class accepts
        self.kw = dict(imgsz=imgsz, conf=conf, iou=iou, half=half, device=device, verbose=False)

    def warmup(self, n: int = 3) -> None:
        dummy = np.zeros((self.kw["imgsz"], self.kw["imgsz"], 3), dtype=np.uint8)
        for _ in range(n):
            self.model.predict(dummy, **self.kw)

    def detect(self, frame: Frame) -> tuple[list[Detection], dict]:
        r = self.model.predict(frame.image, **self.kw)[0]
        dets = []
        if r.boxes is not None and len(r.boxes):
            xyxy = r.boxes.xyxy.cpu().numpy()
            confs = r.boxes.conf.cpu().numpy()
            clss = r.boxes.cls.cpu().numpy().astype(int)
            for (x1, y1, x2, y2), c, k in zip(xyxy, confs, clss):
                name = self.names[k] if k < len(self.names) else r.names.get(k, f"class{k}")
                if c < self.class_conf.get(name, self.conf):
                    continue
                dets.append(Detection(name, float(c), [int(x1), int(y1), int(x2), int(y2)]))
        sp = r.speed
        return dets, {"pre": sp.get("preprocess", 0.0), "infer": sp.get("inference", 0.0),
                      "post": sp.get("postprocess", 0.0)}


def build_detector(cfg: Config, backend: Optional[str] = None):
    v = cfg.section("vision")
    backend = backend or v.get("backend", "tensorrt")
    names = cfg.profile["classes"]
    if backend == "groundtruth":
        return GroundTruthDetector(names)
    if backend not in WEIGHT_FILES:
        raise ValueError(f"unknown vision.backend {backend!r}; choose from {list(WEIGHT_FILES) + ['groundtruth']}")
    weights = cfg.path(v.get("weights_dir", "models/vision/{profile}")) / WEIGHT_FILES[backend]
    return UltralyticsDetector(backend, weights, names, imgsz=int(v.get("imgsz", 640)),
                               conf=float(v.get("conf", 0.25)), iou=float(v.get("iou", 0.5)),
                               half=bool(v.get("half", True)), device=v.get("device", 0),
                               class_conf=cfg.profile.get("class_conf") if v.get("use_class_conf", True) else None)
