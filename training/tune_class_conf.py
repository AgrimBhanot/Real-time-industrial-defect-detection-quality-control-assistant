"""Choose per-class confidence thresholds on the VAL split (never on test).

  python training/tune_class_conf.py --profile pcb --backend torch --min-recall 0.95

For each class: the F1-best threshold among those keeping recall >= --min-recall (or, when the class cannot reach
it, within 0.01 of its recall at vision.conf). Prints a `class_conf:` block for configs/profiles/<profile>.yaml.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from qc.config import load_config  # noqa: E402
from qc.sources import Frame, label_for  # noqa: E402
from qc.vision import build_detector  # noqa: E402
from qc.vision.detector import read_yolo_labels  # noqa: E402
from training.evaluate import images_in, match_same_class, prf  # noqa: E402


def choose(scores: list[tuple[float, bool]], n_gt: int, base: float, min_recall: float) -> float:
    """scores = (confidence, is true positive). Thresholds below `base` are not considered."""
    def at(t):
        tp = sum(h for c, h in scores if c >= t)
        return prf(tp, sum(1 for c, h in scores if c >= t and not h), n_gt - tp)

    floor = min(min_recall, at(base)[1] - 0.01)
    grid = [round(float(t), 2) for t in np.arange(base, 0.86, 0.01)]
    ok = [t for t in grid if at(t)[1] >= floor]
    return max(ok, key=lambda t: (at(t)[2], -t)) if ok else base


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile", default="pcb")
    ap.add_argument("--backend", default="tensorrt")
    ap.add_argument("--split", default="val", choices=["val", "train"])
    ap.add_argument("--min-recall", type=float, default=0.95)
    ap.add_argument("--set", action="append", default=[])
    args = ap.parse_args()
    cfg = load_config(overrides=[f"profile={args.profile}", f"vision.backend={args.backend}",
                                 "vision.use_class_conf=false", *args.set])
    names, base = cfg.profile["classes"], float(cfg.section("vision")["conf"])
    det = build_detector(cfg)
    scores, n_gt = {c: [] for c in names}, dict.fromkeys(names, 0)
    for p in images_in(ROOT / f"data/datasets/{args.profile}/images/{args.split}"):
        img = cv2.imread(str(p))
        h, w = img.shape[:2]
        lbl = label_for(p)
        gts = read_yolo_labels(lbl, w, h, names) if lbl else []
        preds, _ = det.detect(Frame(img, str(p), "tune"))
        _, hits = match_same_class(gts, preds, 0.5)
        for g in gts:
            n_gt[g.defect] += 1
        for d, hit in zip(preds, hits):
            scores[d.defect].append((d.confidence, hit))
    chosen = {c: choose(scores[c], n_gt[c], base, args.min_recall) if n_gt[c] else base for c in names}
    print(f"defects per class in {args.split}: {n_gt}")
    print(yaml.safe_dump({"class_conf": chosen}, sort_keys=False))


if __name__ == "__main__":
    main()
