"""Anomaly detector trained on good parts only (PatchCore-style nearest-neighbour memory bank).

A part that is unlike every good training part raises an unnamed `anomaly` detection. The rule engine treats that as
"needs a person" (REVIEW): it can stop a part from passing but can never FAIL it or overrule a named defect.
Nothing here needs torchvision at run time: backbone and bank live in one TorchScript file (anomaly.pt).
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import cv2
import numpy as np

from qc.schema import Detection
from qc.sources import Frame

ANOMALY = "anomaly"


def peak_box(amap: np.ndarray, thr: float, w: int, h: int) -> tuple[list, float, float]:
    """Box of the above-threshold region holding the peak, in image pixels, plus the peak position."""
    gh, gw = amap.shape
    py, px = np.unravel_index(int(amap.argmax()), amap.shape)
    _, lab = cv2.connectedComponents((amap >= min(thr, float(amap.max()))).astype(np.uint8))
    ys, xs = np.nonzero(lab == lab[py, px])
    box = [round(xs.min() * w / gw), round(ys.min() * h / gh),
           round((xs.max() + 1) * w / gw), round((ys.max() + 1) * h / gh)]
    return box, (px + 0.5) * w / gw, (py + 0.5) * h / gh


def fuse(dets: list[Detection], amap: np.ndarray, score: float, thr: float, w: int, h: int) -> list[Detection]:
    """Append an `anomaly` unless a named defect already covers the peak."""
    if score < thr:
        return dets
    box, cx, cy = peak_box(amap, thr, w, h)
    if any(d.bbox[0] <= cx <= d.bbox[2] and d.bbox[1] <= cy <= d.bbox[3] for d in dets):
        return dets
    conf = 1.0 - 0.5 * thr / score  # 0.5 at the threshold, towards 1 far above it; not a probability
    return dets + [Detection(ANOMALY, float(conf), box)]


class AnomalyModel:
    def __init__(self, folder: Path, device: int | str = 0, half: bool = True):
        import torch

        self.torch = torch
        weights, meta = folder / "anomaly.pt", folder / "anomaly.json"
        for f in (weights, meta):
            if not f.exists():
                raise FileNotFoundError(f"{f} not found; run training/train_anomaly.py or set vision.anomaly=false")
        self.meta = json.loads(meta.read_text())
        self.size, self.products = int(self.meta["size"]), self.meta["products"]
        self.thr = [float(self.meta["thresholds"][p]) for p in self.products]
        self.dev = torch.device(f"cuda:{device}" if isinstance(device, int) else device)
        self.half = half and self.dev.type == "cuda"
        net = torch.jit.load(str(weights), map_location=self.dev).eval()
        self.net = net.half() if self.half else net.float()

    def score(self, bgr: np.ndarray) -> tuple[float, np.ndarray, str, float]:
        """(score, map, product, threshold)"""
        torch = self.torch
        x = cv2.resize(bgr, (self.size, self.size), interpolation=cv2.INTER_AREA)
        t = torch.from_numpy(x).to(self.dev).permute(2, 0, 1)[None]
        with torch.inference_mode():
            amap, votes = self.net(t.half() if self.half else t.float())
        amap = amap.float().cpu().numpy()
        k = int(votes.argmax())
        return float(amap.max()), amap, self.products[k], self.thr[k]


class HybridDetector:
    """Named defects from YOLO, plus `anomaly` where a part is unlike the good ones."""

    def __init__(self, base, model: AnomalyModel):
        self.base, self.model = base, model
        self.backend = f"{base.backend}+anomaly"
        self.class_conf = getattr(base, "class_conf", {})

    def warmup(self, n: int = 3) -> None:
        self.base.warmup(n)
        for _ in range(n):
            self.model.score(np.zeros((64, 64, 3), np.uint8))

    def detect(self, frame: Frame) -> tuple[list[Detection], dict]:
        dets, t = self.base.detect(frame)
        t0 = time.perf_counter()
        h, w = frame.image.shape[:2]
        score, amap, _, thr = self.model.score(frame.image)
        dets = fuse(dets, amap, score, thr, w, h)
        return dets, {**t, "anomaly": (time.perf_counter() - t0) * 1000}


class AnomalyOnly(HybridDetector):
    """vision.anomaly=only: no YOLO (own parts before any labelling)."""

    def __init__(self, model: AnomalyModel):
        self.model, self.backend, self.class_conf = model, "anomaly", {}

    def warmup(self, n: int = 3) -> None:
        for _ in range(n):
            self.model.score(np.zeros((64, 64, 3), np.uint8))

    def detect(self, frame: Frame) -> tuple[list[Detection], dict]:
        t0 = time.perf_counter()
        h, w = frame.image.shape[:2]
        score, amap, _, thr = self.model.score(frame.image)
        ms = (time.perf_counter() - t0) * 1000
        return fuse([], amap, score, thr, w, h), {"pre": 0.0, "infer": ms, "post": 0.0, "anomaly": ms}
