"""Tray inspection: a segmentation model finds nuts, bolts and washers; each part's surface is then checked for rust.

The rust check is a colour rule, not a trained model: the share of a part's surface that is dark orange-brown. It was set
on one camera view under one lamp, so re-check the limits after any lighting or camera change. Bright yellow (zinc
plating, lamp reflections) is excluded by the brightness limit.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from qc.schema import Detection
from qc.sources import Frame


class RustCheck:
    def __init__(self, hue=(4, 24), min_sat: int = 60, value=(35, 150), min_part_frac: float = 0.03, erode: int = 9):
        self.hue, self.min_sat, self.value = hue, min_sat, value
        self.min_part_frac, self.erode = min_part_frac, erode

    def __call__(self, crop: np.ndarray, mask: np.ndarray) -> Optional[tuple]:
        """(share of surface, box of the rusty area inside the crop) or None."""
        k = np.ones((self.erode, self.erode), np.uint8)
        inner = cv2.erode(mask, k, borderValue=0)
        n = int(np.count_nonzero(inner))
        if n < 200:
            return None
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        lo = np.array([self.hue[0], self.min_sat, self.value[0]], np.uint8)
        hi = np.array([self.hue[1], 255, self.value[1]], np.uint8)
        rust = cv2.bitwise_and(cv2.inRange(hsv, lo, hi), inner)
        rust = cv2.morphologyEx(rust, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        frac = np.count_nonzero(rust) / n
        if frac < self.min_part_frac:
            return None
        ys, xs = np.nonzero(rust)
        x1, x2 = np.percentile(xs, (2, 98))
        y1, y2 = np.percentile(ys, (2, 98))
        return frac, [int(x1), int(y1), int(x2) + 1, int(y2) + 1]


class TrayDetector:
    """Part finder + per-part checks. Sets frame.parts and returns the defects as detections."""

    def __init__(self, backend: str, weights: Path, names: list, imgsz: int = 640, conf: float = 0.6, iou: float = 0.5,
                 half: bool = True, device=0, tray: Optional[dict] = None):
        if not weights.exists():
            raise FileNotFoundError(f"{backend} weights not found: {weights}\n  train the part finder first "
                                    "(training/make_tray_dataset.py), then training/export.py --profile tray --to engine")
        from ultralytics import YOLO

        tray = tray or {}
        self.backend, self.names = backend, names
        self.model = YOLO(str(weights), task="segment")
        self.kw = dict(imgsz=imgsz, conf=conf, iou=iou, half=half, device=device, verbose=False)
        self.roi = tray.get("roi", [0.0, 0.0, 1.0, 1.0])
        self.rust = RustCheck(**tray.get("rust", {}))
        self.class_conf: dict = {}

    def warmup(self, n: int = 3) -> None:
        blank = np.zeros((self.kw["imgsz"], self.kw["imgsz"], 3), np.uint8)
        for _ in range(n):
            self.model.predict(blank, **self.kw)

    def detect(self, frame: Frame) -> tuple[list[Detection], dict]:
        img = frame.image
        h, w = img.shape[:2]
        r = self.model.predict(img, **self.kw)[0]
        t0 = time.perf_counter()
        found = []
        if r.boxes is not None and len(r.boxes) and r.masks is not None:
            for box, c, k, poly in zip(r.boxes.xyxy.cpu().numpy(), r.boxes.conf.cpu().numpy(),
                                       r.boxes.cls.cpu().numpy().astype(int), r.masks.xy):
                found.append((box, float(c), self.names[k], poly))
        dets = self.check(frame, found)
        sp = r.speed
        return dets, {"pre": sp.get("preprocess", 0.0), "infer": sp.get("inference", 0.0),
                      "post": sp.get("postprocess", 0.0), "checks": (time.perf_counter() - t0) * 1000}

    def check(self, frame: Frame, found: list) -> list[Detection]:
        """found: [(box, confidence, type, polygon)] -> defects; numbers the parts left to right."""
        img = frame.image
        h, w = img.shape[:2]
        rx1, ry1, rx2, ry2 = self.roi[0] * w, self.roi[1] * h, self.roi[2] * w, self.roi[3] * h
        dets, parts, count = [], [], {}
        for box, conf, kind, poly in sorted(found, key=lambda f: (f[0][0], f[0][1])):
            x1, y1, x2, y2 = (int(v) for v in box)
            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
            if not (rx1 <= cx <= rx2 and ry1 <= cy <= ry2):
                continue
            x1, y1, x2, y2 = max(0, x1), max(0, y1), min(w, x2), min(h, y2)
            count[kind] = count.get(kind, 0) + 1
            pid = f"{kind} {count[kind]}"
            cut = x1 <= 2 or y1 <= 2 or x2 >= w - 2 or y2 >= h - 2
            poly = np.asarray(poly, np.float32).reshape(-1, 2)
            parts.append({"id": pid, "type": kind, "confidence": round(conf, 3), "bbox": [x1, y1, x2, y2],
                          "cut_off": cut, "poly": np.round(poly[:: max(1, len(poly) // 60)]).astype(int).tolist()})
            if x2 - x1 < 8 or y2 - y1 < 8 or len(poly) < 3:
                continue
            mask = np.zeros((y2 - y1, x2 - x1), np.uint8)
            cv2.fillPoly(mask, [np.round(poly - (x1, y1)).astype(np.int32)], 255)
            hit = self.rust(img[y1:y2, x1:x2], mask)
            if hit:
                frac, (a, b, c, d) = hit
                # a strength score, not a probability: 0.5 at the limit, towards 1 for a fully rusty part
                score = min(0.99, 0.5 + 0.5 * min(1.0, frac / 0.5))
                dets.append(Detection("rust", score, [x1 + a, y1 + b, x1 + c, y1 + d], size=float(frac),
                                      size_unit="part_frac", part=pid))
        frame.parts = parts
        return dets
