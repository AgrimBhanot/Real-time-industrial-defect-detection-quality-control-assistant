"""Photograph physical parts from a USB or CSI camera, recording which part and its true condition.

  python training/capture_images.py --out data/raw/captures/day1 --shots 4

Prompts for "<part id> <condition>" (e.g. `B017 rust`, `B018 good`), then saves --shots photos, waiting for Enter
before each so the part can be turned. Conditions: good or a class of the profile. Empty line = finish.
Label in CVAT / Label Studio, export YOLO, then run training/prepare_fasteners.py.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from qc.config import load_profile  # noqa: E402
from qc.sources import CameraSource, center_square  # noqa: E402
from training.parts import check_part  # noqa: E402


def grab(cap, crop: str, flush: int = 8):
    """Newest frame: frames buffered while waiting for the operator are discarded."""
    for _ in range(flush):
        cap.grab()
    ok, img = cap.read()
    if not ok:
        raise RuntimeError("camera read failed")
    return center_square(img) if crop == "square" else img


def ask_part(classes: list[str]):
    """(part, condition) or None when the operator is done."""
    while True:
        line = input("part and condition (empty = finish): ").split()
        if not line:
            return None
        if len(line) == 2 and line[1] in ("good", *classes):
            try:
                return check_part(line[0]), line[1]
            except ValueError as exc:
                print(exc)
                continue
        print(f"type: <part id> <condition>; conditions: good, {', '.join(classes)}")


def add_camera_args(ap: argparse.ArgumentParser) -> None:
    ap.add_argument("--profile", default="fasteners")
    ap.add_argument("--kind", choices=["usb", "csi"], default="usb")
    ap.add_argument("--index", type=int, default=0)
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=720)
    ap.add_argument("--crop", choices=["square", "none"], default="square")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=f"data/raw/captures/{datetime.now():%Y%m%d_%H%M%S}")
    ap.add_argument("--shots", type=int, default=4)
    add_camera_args(ap)
    args = ap.parse_args()
    classes = load_profile(args.profile)["classes"]
    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    cap = CameraSource(args.kind, args.index, args.width, args.height)._open()
    n = 0
    try:
        while (pc := ask_part(classes)) is not None:
            for i in range(args.shots):
                input(f"  {pc[0]} shot {i + 1}/{args.shots}: place / turn the part, then Enter ")
                path = out / f"{pc[0]}__{pc[1]}__{datetime.now():%m%d%H%M%S%f}.jpg"
                cv2.imwrite(str(path), grab(cap, args.crop), [cv2.IMWRITE_JPEG_QUALITY, 95])
                n += 1
    finally:
        cap.release()
    print(f"saved {n} images to {out}")


if __name__ == "__main__":
    main()
