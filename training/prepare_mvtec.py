"""MVTec AD screw + metal_nut -> YOLO boxes, with our own stratified split (70/15/15 of the defective images).

  python training/prepare_mvtec.py --src ../mvtec     # holds screw/ and metal_nut/ (any nesting)

MVTec keeps every defective image in its test folder, so results are NOT comparable with published MVTec numbers.
test_clean = MVTec's test/good. train/good is divided 85/15 between train and val.
"""
from __future__ import annotations

import argparse
import json
import random
import shutil
import sys
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from qc.config import load_profile  # noqa: E402

CLASS_OF = {
    ("screw", "manipulated_front"): "tip_damage", ("screw", "scratch_head"): "scratch",
    ("screw", "scratch_neck"): "scratch", ("screw", "thread_side"): "thread_damage",
    ("screw", "thread_top"): "thread_damage", ("metal_nut", "bent"): "bent",
    ("metal_nut", "color"): "discolouration", ("metal_nut", "flip"): "flipped", ("metal_nut", "scratch"): "scratch",
}


def mask_boxes(mask: np.ndarray, merge_frac: float = 0.03, min_px: int = 20) -> list[tuple]:
    """Boxes of the mask regions; regions closer than merge_frac of the image side become one box."""
    m = (mask > 127).astype(np.uint8)
    k = max(1, round(merge_frac * max(m.shape))) | 1
    n, lab = cv2.connectedComponents(cv2.dilate(m, np.ones((k, k), np.uint8)))
    out = []
    for i in range(1, n):
        ys, xs = np.nonzero(m & (lab == i))
        if len(xs) >= min_px:
            out.append((int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))
    return out


def split_list(items: list, rng: random.Random, val: float, test: float) -> dict:
    items = sorted(items)
    rng.shuffle(items)
    nt, nv = round(test * len(items)), round(val * len(items))
    return {"test": items[:nt], "val": items[nt:nt + nv], "train": items[nt + nv:]}


def build(src: Path, out: Path, names: list[str], seed: int = 0) -> dict:
    roots = {c: next((p.parents[1] for p in sorted(src.rglob(f"{c}/train/good"))), None) for c in ("screw", "metal_nut")}
    missing = [c for c, r in roots.items() if r is None]
    if missing:
        raise ValueError(f"not found under {src}: {missing}")
    rng, plan = random.Random(seed), []
    for (cat, defect), cls in CLASS_OF.items():
        for s, files in split_list((roots[cat] / "test" / defect).glob("*.png"), rng, 0.15, 0.15).items():
            plan += [(f, s, cat, defect, cls) for f in files]
    for cat, root in roots.items():
        for s, files in split_list((root / "train/good").glob("*.png"), rng, 0.15, 0.0).items():
            plan += [(f, s, cat, "good", None) for f in files]
        plan += [(f, "test_clean", cat, "good", None) for f in sorted((root / "test/good").glob("*.png"))]
    if out.exists():
        shutil.rmtree(out)
    counts = Counter()
    for f, s, cat, defect, cls in plan:
        img = cv2.imread(str(f))
        rows = []
        if cls:
            mask = cv2.imread(str(roots[cat] / "ground_truth" / defect / f"{f.stem}_mask.png"), cv2.IMREAD_GRAYSCALE)
            if mask is None or mask.shape != img.shape[:2]:
                raise ValueError(f"mask missing or wrong size for {f}")
            h, w = mask.shape
            rows = [f"{names.index(cls)} {(x1 + x2) / 2 / w:.6f} {(y1 + y2) / 2 / h:.6f} {(x2 - x1) / w:.6f} "
                    f"{(y2 - y1) / h:.6f}" for x1, y1, x2, y2 in mask_boxes(mask)]
            if not rows:
                raise ValueError(f"empty mask for {f}")
        stem = f"{cat}_{defect}_{'test' if s == 'test_clean' else 'tr' if defect == 'good' else 'd'}_{f.stem}"
        for kind in ("images", "labels"):
            (out / kind / s).mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(out / "images" / s / f"{stem}.png"), img)
        (out / "labels" / s / f"{stem}.txt").write_text("\n".join(rows) + ("\n" if rows else ""))
        counts[f"{s}/{cls or 'good'}"] += 1
    (out / "dataset.yaml").write_text(yaml.safe_dump({
        "path": str(out), "train": "images/train", "val": "images/val", "test": "images/test",
        "names": dict(enumerate(names))}, sort_keys=False))
    return dict(sorted(counts.items()))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    out = ROOT / "data/datasets/mvtec_fasteners"
    try:
        print(json.dumps(build(Path(a.src).resolve(), out, load_profile("mvtec_fasteners")["classes"], a.seed), indent=1))
    except ValueError as exc:
        sys.exit(str(exc))


if __name__ == "__main__":
    main()
