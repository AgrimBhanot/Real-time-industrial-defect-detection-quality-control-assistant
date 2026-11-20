"""Collect your own images from a USB or CSI camera (for the fasteners profile, or real PCB photos).

  python training/capture_images.py --out data/raw/captures/bolts_day1 --interval 2 --count 200
  python training/capture_images.py --preview          # SPACE saves, q quits (needs the VNC desktop)

Label the result in CVAT / Label Studio / Roboflow and export in YOLO format into
data/datasets/<profile>/{images,labels}/{train,val,test}.
"""
from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from qc.sources import CameraSource  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=f"data/raw/captures/{datetime.now():%Y%m%d_%H%M%S}")
    ap.add_argument("--kind", choices=["usb", "csi"], default="usb")
    ap.add_argument("--index", type=int, default=0)
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=720)
    ap.add_argument("--interval", type=float, default=0.0, help="seconds between automatic saves (0 = manual)")
    ap.add_argument("--count", type=int, default=100)
    ap.add_argument("--preview", action="store_true")
    args = ap.parse_args()
    if not args.preview and args.interval <= 0:
        sys.exit("use --interval N for headless capture, or --preview for manual capture")

    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    saved, last = 0, 0.0
    for frame in CameraSource(args.kind, args.index, args.width, args.height, 30):
        now = time.time()
        save = args.interval > 0 and now - last >= args.interval
        if args.preview:
            cv2.imshow("capture (SPACE save, q quit)", frame.image)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            save = save or key == ord(" ")
        if save:
            path = out / f"{datetime.now():%H%M%S_%f}.jpg"
            cv2.imwrite(str(path), frame.image, [cv2.IMWRITE_JPEG_QUALITY, 95])
            saved, last = saved + 1, now
            print(f"[{saved}/{args.count}] {path.name}")
            if saved >= args.count:
                break
    cv2.destroyAllWindows()
    print(f"saved {saved} images to {out}")


if __name__ == "__main__":
    main()
