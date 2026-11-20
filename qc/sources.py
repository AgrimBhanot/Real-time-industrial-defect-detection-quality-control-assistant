"""Frame sources: image folder (simulated conveyor of real images), video file, or USB/CSI camera."""
from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, Optional

import cv2
import numpy as np

from qc.config import Config

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}


@dataclass
class Frame:
    image: np.ndarray
    ref: str
    source: str
    label_path: Optional[str] = None
    t_captured: float = field(default_factory=time.perf_counter)


def label_for(image_path: Path) -> Optional[Path]:
    """YOLO label for an image: <split>/images/x.jpg -> <split>/labels/x.txt, else x.txt beside it."""
    parts = list(image_path.parts)
    if "images" in parts:
        i = len(parts) - 1 - parts[::-1].index("images")
        candidate = Path(*parts[:i], "labels", *parts[i + 1:]).with_suffix(".txt")
        if candidate.exists():
            return candidate
    beside = image_path.with_suffix(".txt")
    return beside if beside.exists() else None


class FolderSource:
    def __init__(self, folder: Path, shuffle: bool = True, loop: bool = True, seed: Optional[int] = None):
        self.files = sorted(p for p in Path(folder).rglob("*") if p.suffix.lower() in IMAGE_EXTS)
        if not self.files:
            raise FileNotFoundError(f"no images found under {folder}")
        self.shuffle, self.loop = shuffle, loop
        self.rng = random.Random(seed)

    def __iter__(self) -> Iterator[Frame]:
        while True:
            order = list(self.files)
            if self.shuffle:
                self.rng.shuffle(order)
            for p in order:
                img = cv2.imread(str(p))
                if img is None:
                    continue
                lbl = label_for(p)
                yield Frame(img, str(p), "sim_conveyor", str(lbl) if lbl else None)
            if not self.loop:
                return


class VideoSource:
    def __init__(self, path: Path, loop: bool = True):
        self.path, self.loop = str(path), loop

    def __iter__(self) -> Iterator[Frame]:
        while True:
            cap = cv2.VideoCapture(self.path)
            if not cap.isOpened():
                raise RuntimeError(f"cannot open video {self.path}")
            idx = 0
            while True:
                ok, img = cap.read()
                if not ok:
                    break
                yield Frame(img, f"{self.path}#{idx}", "video")
                idx += 1
            cap.release()
            if not self.loop:
                return


def csi_pipeline(width: int, height: int, fps: int, sensor_id: int = 0) -> str:
    return (
        f"nvarguscamerasrc sensor-id={sensor_id} ! "
        f"video/x-raw(memory:NVMM),width={width},height={height},framerate={fps}/1 ! "
        "nvvidconv ! video/x-raw,format=BGRx ! videoconvert ! video/x-raw,format=BGR ! "
        "appsink drop=1 max-buffers=1"
    )


class CameraSource:
    def __init__(self, kind: str = "usb", index: int = 0, width: int = 1280, height: int = 720, fps: int = 30):
        self.kind, self.index, self.width, self.height, self.fps = kind, index, width, height, fps

    def _open(self) -> cv2.VideoCapture:
        if self.kind == "csi":
            cap = cv2.VideoCapture(csi_pipeline(self.width, self.height, self.fps, self.index), cv2.CAP_GSTREAMER)
        else:
            cap = cv2.VideoCapture(self.index, cv2.CAP_V4L2)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            cap.set(cv2.CAP_PROP_FPS, self.fps)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        if not cap.isOpened():
            raise RuntimeError(f"cannot open {self.kind} camera {self.index}")
        return cap

    def __iter__(self) -> Iterator[Frame]:
        cap = self._open()
        idx = 0
        try:
            while True:
                ok, img = cap.read()
                if not ok:
                    raise RuntimeError("camera read failed")
                yield Frame(img, f"camera:{self.kind}:{self.index}#{idx}", "camera")
                idx += 1
        finally:
            cap.release()


def build_source(cfg: Config):
    s = cfg.section("source")
    kind = s.get("type", "folder")
    if kind == "folder":
        return FolderSource(cfg.path(s["path"]), shuffle=s.get("shuffle", True), loop=s.get("loop", True),
                            seed=s.get("seed"))
    if kind == "video":
        return VideoSource(cfg.path(s["path"]), loop=s.get("loop", True))
    if kind == "camera":
        c = s.get("camera", {})
        return CameraSource(c.get("kind", "usb"), int(c.get("index", 0)), int(c.get("width", 1280)),
                            int(c.get("height", 720)), int(c.get("fps", 30)))
    raise ValueError(f"unknown source.type {kind!r}")
