"""Derive per-class size thresholds [P33, P66] from training labels -> configs/profiles/<profile>.size_thresholds.json.

  python training/calibrate_severity.py --profile pcb

Sizes use the profile's unit: mm^2 when px_per_mm is set, otherwise fraction of the frame area.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from qc.config import PROFILES_DIR, load_profile  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile", default="pcb")
    ap.add_argument("--split", default="train")
    ap.add_argument("--low", type=float, default=33)
    ap.add_argument("--high", type=float, default=66)
    args = ap.parse_args()

    prof = load_profile(args.profile)
    names, ppm = prof["classes"], prof.get("px_per_mm")
    ds = ROOT / f"data/datasets/{args.profile}"
    sizes: dict[str, list[float]] = defaultdict(list)
    for lbl in sorted((ds / "labels" / args.split).glob("*.txt")):
        rows = [r.split() for r in lbl.read_text().splitlines() if r.strip()]
        if not rows:
            continue
        img = next((ds / "images" / args.split).glob(f"{lbl.stem}.*"), None)
        if img is None:
            continue
        h, w = cv2.imread(str(img), cv2.IMREAD_GRAYSCALE).shape[:2]
        for r in rows:
            cls, bw, bh = int(r[0]), float(r[3]), float(r[4])
            area = bw * w * bh * h
            sizes[names[cls]].append(area / ppm**2 if ppm else area / (w * h))

    out = {}
    rules = prof["severity"]["classes"]
    for cls in names:
        vals = np.array(sizes.get(cls, []))
        if len(vals):
            print(f"{cls:>14}: n={len(vals):5d}  P{args.low:.0f}={np.percentile(vals, args.low):.5f}  "
                  f"P{args.high:.0f}={np.percentile(vals, args.high):.5f}  max={vals.max():.5f}")
        if rules.get(cls, {}).get("size_rule") and len(vals):
            out[cls] = [round(float(np.percentile(vals, args.low)), 6), round(float(np.percentile(vals, args.high)), 6)]
    path = PROFILES_DIR / f"{args.profile}.size_thresholds.json"
    path.write_text(json.dumps(out, indent=2))
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
