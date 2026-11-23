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


def center_square(img: np.ndarray) -> np.ndarray:
    """Largest centred square, so a 640 model input is not spent on letterbox bars."""
    h, w = img.shape[:2]
    s = min(h, w)
    y, x = (h - s) // 2, (w - s) // 2
    return img[y:y + s, x:x + s].copy()


class StableTrigger:
    """Turns a camera stream into units: fires once when the scene has changed and then held still.

    The reference is the last fired view, so a part resting under the camera is inspected only once.
    """

    def __init__(self, change: float = 8.0, still: float = 2.0, frames: int = 5):
        self.change, self.still, self.frames = change, still, frames
        self.prev = self.ref = None
        self.n_still = 0

    def update(self, img: np.ndarray) -> bool:
        g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
        g = cv2.GaussianBlur(cv2.resize(g, (160, 120), interpolation=cv2.INTER_AREA), (5, 5), 0)
        prev, self.prev = self.prev, g
        if prev is None or float(cv2.absdiff(g, prev).mean()) > self.still:
            self.n_still = 0
            return False
        self.n_still += 1
        if self.n_still < self.frames:
            return False
        if self.ref is not None and float(cv2.absdiff(g, self.ref).mean()) < self.change:
            return False
        self.ref = g
        return True


class CameraSource:
    def __init__(self, kind: str = "usb", index: int = 0, width: int = 1280, height: int = 720, fps: int = 30,
                 trigger: Optional[StableTrigger] = None, reconnect_s: float = 0.0, crop: str = "none"):
        if crop not in ("none", "square"):
            raise ValueError(f"camera crop must be none or square, got {crop!r}")
        self.crop = crop
        self.trigger, self.reconnect_s = trigger, reconnect_s
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

    def _reopen(self) -> cv2.VideoCapture:
        """Retry for up to reconnect_s seconds (0 = fail at once)."""
        deadline = time.monotonic() + self.reconnect_s
        while time.monotonic() < deadline:
            try:
                cap = self._open()
                if cap.read()[0]:  # some drivers reopen a dead device; only a frame proves it is back
                    return cap
                cap.release()
            except RuntimeError:
                pass
            time.sleep(min(0.5, self.reconnect_s))
        raise RuntimeError(f"camera read failed ({self.kind} {self.index})")

    def __iter__(self) -> Iterator[Frame]:
        cap = self._open()
        idx = 0
        try:
            while True:
                ok, img = cap.read()
                if not ok:
                    cap.release()
                    cap = self._reopen()
                    continue
                if self.crop == "square":
                    img = center_square(img)
                if self.trigger is not None and not self.trigger.update(img):
                    continue
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
                            int(c.get("height", 720)), int(c.get("fps", 30)),
                            trigger=StableTrigger(**(c.get("trigger_params") or {}))
                            if c.get("trigger", "none") == "stable" else None,
                            reconnect_s=float(c.get("reconnect_s", 0)), crop=c.get("crop", "none"))
    raise ValueError(f"unknown source.type {kind!r}")
