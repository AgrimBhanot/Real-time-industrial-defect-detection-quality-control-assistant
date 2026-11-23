"""Labelled captures -> YOLO dataset, split by PHYSICAL PART so no part is in both training and test.

  python training/prepare_fasteners.py --images data/raw/captures/day1 --labels data/raw/labels/day1

Checks every photo: defective parts need a label file, good parts must have none (or an empty one).
A photo of a defective part with an EMPTY label file is kept: the defect may face away from the camera.
"""
from __future__ import annotations

import argparse
import json
import random
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from qc.config import load_profile  # noqa: E402
from qc.sources import IMAGE_EXTS  # noqa: E402
from training.parts import parse_name  # noqa: E402


def split_parts(conditions: dict[str, set], val: float, test: float, seed: int) -> dict[str, str]:
    """part -> split, stratified by condition. Every condition needs >= 3 parts."""
    strata = defaultdict(list)
    for part, conds in sorted(conditions.items()):
        strata["+".join(sorted(conds))].append(part)
    rng, out = random.Random(seed), {}
    for cond, parts in sorted(strata.items()):
        if len(parts) < 3:
            raise ValueError(f"condition {cond!r} has {len(parts)} part(s); need at least 3 (train/val/test)")
        rng.shuffle(parts)
        n_test = max(1, round(test * len(parts)))
        n_val = max(1, round(val * len(parts)))
        if n_test + n_val >= len(parts):
            n_test = n_val = 1
        for i, p in enumerate(parts):
            out[p] = "test" if i < n_test else "val" if i < n_test + n_val else "train"
    return out


def check_label(path: Path, n_classes: int) -> list[str]:
    rows = [r for r in path.read_text().splitlines() if r.strip()] if path.exists() else []
    for r in rows:
        v = r.split()
        if len(v) != 5 or not v[0].isdigit() or int(v[0]) >= n_classes or not all(0 <= float(x) <= 1 for x in v[1:]):
            raise ValueError(f"{path.name}: bad YOLO row {r!r}")
    return rows


def build(images: list[Path], labels: list[Path], out: Path, profile: dict, val=0.2, test=0.2, seed=0) -> dict:
    files, conds, problems = [], defaultdict(set), []
    for d, ld in zip(images, labels, strict=True):
        for img in sorted(p for p in d.iterdir() if p.suffix.lower() in IMAGE_EXTS):
            try:
                part, cond = parse_name(img.stem)
                lbl = ld / f"{img.stem}.txt"
                rows = check_label(lbl, len(profile["classes"]))
            except ValueError as exc:
                problems.append(str(exc))
                continue
            if cond == "good" and rows:
                problems.append(f"{img.name}: good part but has labels")
            elif cond != "good" and not lbl.exists():
                problems.append(f"{img.name}: {cond} part but no label file")
            elif cond != "good" and cond not in profile["classes"]:
                problems.append(f"{img.name}: unknown condition {cond}")
            files.append((img, part, cond, rows))
            conds[part].add(cond)
    if problems:
        raise ValueError(f"{len(problems)} problem(s):\n  " + "\n  ".join(problems[:30]))
    if not files:
        raise ValueError("no images found")
    both = [p for p, c in conds.items() if len(c) > 1]
    if both:
        raise ValueError(f"parts recorded with several conditions (give a damaged part a new id?): {both}")
    split = split_parts(conds, val, test, seed)
    if out.exists():
        shutil.rmtree(out)
    counts, group_of = Counter(), {}
    for img, part, cond, rows in files:
        s = split[part]
        # an unlabelled view of a defective test part is neither a clean unit nor a visible defect: leave it out
        if s == "test" and cond != "good" and not rows:
            counts["test_skipped_no_visible_defect"] += 1
            continue
        s = "test_clean" if s == "test" and cond == "good" else s
        for kind in ("images", "labels"):
            (out / kind / s).mkdir(parents=True, exist_ok=True)
        shutil.copy2(img, out / "images" / s / img.name)
        (out / "labels" / s / f"{img.stem}.txt").write_text("\n".join(rows) + ("\n" if rows else ""))
        counts[s] += 1
        group_of[img.stem] = part
    (out / "dataset.yaml").write_text(yaml.safe_dump({
        "path": str(out), "train": "images/train", "val": "images/val", "test": "images/test",
        "names": dict(enumerate(profile["classes"]))}, sort_keys=False))
    (out / "groups.json").write_text(json.dumps({
        "train_groups": sorted(p for p, s in split.items() if s == "train"),
        "val_groups": sorted(p for p, s in split.items() if s == "val"),
        "test_groups": sorted(p for p, s in split.items() if s == "test"), "group_of": group_of}, indent=1))
    return dict(counts)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--images", nargs="+", required=True)
    ap.add_argument("--labels", nargs="+", required=True, help="one label folder per image folder, same order")
    ap.add_argument("--profile", default="fasteners")
    ap.add_argument("--val", type=float, default=0.2)
    ap.add_argument("--test", type=float, default=0.2)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    try:
        counts = build([ROOT / p for p in a.images], [ROOT / p for p in a.labels],
                       ROOT / f"data/datasets/{a.profile}", load_profile(a.profile), a.val, a.test, a.seed)
    except ValueError as exc:
        sys.exit(str(exc))
    print("images:", counts)


if __name__ == "__main__":
    main()
