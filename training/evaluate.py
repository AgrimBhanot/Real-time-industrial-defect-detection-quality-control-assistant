"""Evaluate the detector + rule engine on a held-out split, with the same code path the device uses.

  python training/evaluate.py --profile pcb --backend tensorrt          # on the Jetson (report these)
  python training/evaluate.py --profile pcb --backend torch --map       # on Colab, plus Ultralytics mAP

Reports (JSON + Markdown in bench/results/):
  - per-class and macro precision / recall / F1 at a stated IoU and confidence threshold
  - recall on hard cases (smallest-quartile defects per class)
  - class confusion matrix (incl. missed / background)
  - unit-level: defective units passed (escapes), clean units rejected (false rejects), verdict agreement
  - vision latency mean / p95 on this machine
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from qc.config import load_config  # noqa: E402
from qc.rules import RuleEngine  # noqa: E402
from qc.sources import IMAGE_EXTS, Frame, label_for  # noqa: E402
from qc.vision import build_detector  # noqa: E402
from qc.vision.detector import read_yolo_labels  # noqa: E402

PASSING = ("PASS", "PASS_WITH_NOTE")


def iou(a, b) -> float:
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


def match_same_class(gts, preds, thr):
    """Greedy by confidence. Returns matched gt flags, matched pred flags."""
    g_hit, p_hit = [False] * len(gts), [False] * len(preds)
    for pi in sorted(range(len(preds)), key=lambda i: -preds[i].confidence):
        best, bj = thr, -1
        for gi, g in enumerate(gts):
            if not g_hit[gi] and g.defect == preds[pi].defect:
                v = iou(g.bbox, preds[pi].bbox)
                if v >= best:
                    best, bj = v, gi
        if bj >= 0:
            g_hit[bj], p_hit[pi] = True, True
    return g_hit, p_hit


def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return p, r, (2 * p * r / (p + r) if p + r else 0.0)


def images_in(d: Path) -> list[Path]:
    return sorted(p for p in d.glob("*") if p.suffix.lower() in IMAGE_EXTS) if d.exists() else []


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile", default="pcb")
    ap.add_argument("--backend", default=None, help="tensorrt | onnxruntime | torch | groundtruth")
    ap.add_argument("--split", default="test")
    ap.add_argument("--clean-split", default="test_clean", help="defect-free images for false-reject rate")
    ap.add_argument("--conf", type=float, default=None, help="confidence threshold (default from config)")
    ap.add_argument("--iou", type=float, default=0.5, help="IoU threshold for a true positive")
    ap.add_argument("--map", action="store_true", help="also run Ultralytics val() for mAP@0.5 / mAP@0.5:0.95")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--set", action="append", default=[])
    args = ap.parse_args()

    overrides = [f"profile={args.profile}", *args.set]
    if args.backend:
        overrides.append(f"vision.backend={args.backend}")
    if args.conf is not None:
        overrides.append(f"vision.conf={args.conf}")
    cfg = load_config(overrides=overrides)
    names = cfg.profile["classes"]
    det = build_detector(cfg)
    det.warmup()
    rules = RuleEngine(cfg.profile)
    ds = ROOT / f"data/datasets/{args.profile}"

    units = [(p, False) for p in images_in(ds / "images" / args.split)]
    units += [(p, True) for p in images_in(ds / "images" / args.clean_split)]
    if args.limit:
        units = units[: args.limit]
    if not units:
        sys.exit(f"no images in {ds / 'images' / args.split}")

    tp, fp, fn = defaultdict(int), defaultdict(int), defaultdict(int)
    gt_sizes = []  # (class, area_px, matched)
    confusion = defaultdict(lambda: defaultdict(int))
    verdicts = defaultdict(lambda: defaultdict(int))
    escapes = false_rejects = n_defective = n_clean = 0
    lat = []
    for img_path, is_clean in units:
        img = cv2.imread(str(img_path))
        h, w = img.shape[:2]
        lbl = label_for(img_path)
        gts = read_yolo_labels(lbl, w, h, names) if lbl else []
        t0 = time.perf_counter()
        preds, _ = det.detect(Frame(img, str(img_path), "eval", str(lbl) if lbl else None))
        lat.append((time.perf_counter() - t0) * 1000)

        g_hit, p_hit = match_same_class(gts, preds, args.iou)
        for g, hit in zip(gts, g_hit):
            (tp if hit else fn)[g.defect] += 1
            gt_sizes.append((g.defect, g.area_px, hit))
        for p, hit in zip(preds, p_hit):
            if not hit:
                fp[p.defect] += 1

        used = set()
        for g in gts:
            cands = [(iou(g.bbox, p.bbox), i) for i, p in enumerate(preds) if i not in used]
            v, i = max(cands, default=(0.0, -1))
            if v >= args.iou:
                used.add(i)
                confusion[g.defect][preds[i].defect] += 1
            else:
                confusion[g.defect]["missed"] += 1
        for i, p in enumerate(preds):
            if i not in used:
                confusion["background"][p.defect] += 1

        rules.annotate(preds, w, h)
        pred_v, _ = rules.decide(preds)
        rules.annotate(gts, w, h)
        gt_v, _ = rules.decide(gts) if gts else ("PASS", [])
        verdicts[gt_v][pred_v] += 1
        if gts and not is_clean:
            n_defective += 1
            escapes += pred_v in PASSING
        if is_clean or not gts:
            n_clean += 1
            false_rejects += pred_v not in PASSING

    per_class, hard_all = {}, []
    for c in names:
        p, r, f = prf(tp[c], fp[c], fn[c])
        sizes = [a for k, a, _ in gt_sizes if k == c]
        hard = None
        if sizes:
            q1 = float(np.percentile(sizes, 25))
            hits = [m for k, a, m in gt_sizes if k == c and a <= q1]
            hard_all += hits
            hard = sum(hits) / len(hits) if hits else None
        per_class[c] = {"tp": tp[c], "fp": fp[c], "fn": fn[c], "precision": p, "recall": r, "f1": f,
                        "hard_case_recall": hard}
    present = [c for c in names if tp[c] + fn[c] > 0]
    macro = {k: float(np.mean([per_class[c][k] for c in present])) if present else 0.0
             for k in ("precision", "recall", "f1")}
    report = {
        "profile": args.profile, "backend": det.backend, "split": args.split, "clean_split": args.clean_split,
        "iou_threshold": args.iou, "conf_threshold": cfg.section("vision").get("conf"),
        "n_images": len(units), "n_defective_units": n_defective, "n_clean_units": n_clean,
        "per_class": per_class, "macro": macro,
        "hard_case_recall_overall": (sum(hard_all) / len(hard_all)) if hard_all else None,
        "unit_level": {
            "escape_rate": escapes / n_defective if n_defective else None,
            "false_reject_rate": false_rejects / n_clean if n_clean else None,
            "verdict_matrix_gt_to_pred": {k: dict(v) for k, v in verdicts.items()},
        },
        "confusion_gt_to_pred": {k: dict(v) for k, v in confusion.items()},
        "latency_ms": {"mean": float(np.mean(lat)), "p50": float(np.percentile(lat, 50)),
                       "p95": float(np.percentile(lat, 95))},
        "evaluated_at": datetime.now().isoformat(timespec="seconds"),
    }
    if args.map and det.backend != "groundtruth":
        from ultralytics import YOLO

        m = YOLO(str(cfg.path(cfg.section("vision")["weights_dir"]) / "best.pt"))
        r = m.val(data=str(ds / "dataset.yaml"), split=args.split, imgsz=cfg.section("vision").get("imgsz", 640),
                  verbose=False)
        report["ultralytics"] = {"map50": float(r.box.map50), "map50_95": float(r.box.map)}

    out = ROOT / "bench/results"
    out.mkdir(parents=True, exist_ok=True)
    stem = f"eval_{args.profile}_{det.backend}_{datetime.now():%m%d_%H%M}"
    (out / f"{stem}.json").write_text(json.dumps(report, indent=2))
    md = [f"### Detection on `{args.split}` ({det.backend}, IoU>={args.iou}, conf>={report['conf_threshold']})", "",
          "| class | P | R | F1 | hard-case R | TP | FP | FN |", "|---|---|---|---|---|---|---|---|"]
    for c, v in per_class.items():
        hc = "-" if v["hard_case_recall"] is None else f"{v['hard_case_recall']:.3f}"
        md.append(f"| {c} | {v['precision']:.3f} | {v['recall']:.3f} | {v['f1']:.3f} | {hc} | {v['tp']} | {v['fp']} | {v['fn']} |")
    md.append(f"| **macro** | {macro['precision']:.3f} | {macro['recall']:.3f} | {macro['f1']:.3f} | | | | |")
    u = report["unit_level"]
    fmt = lambda x: "-" if x is None else f"{100 * x:.1f}%"  # noqa: E731
    md += ["", f"Unit level: escape rate {fmt(u['escape_rate'])} of {n_defective} defective units; "
               f"false-reject rate {fmt(u['false_reject_rate'])} of {n_clean} clean units.",
           f"Vision latency: mean {report['latency_ms']['mean']:.1f} ms, p95 {report['latency_ms']['p95']:.1f} ms."]
    (out / f"{stem}.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    print(f"\nwrote {out / stem}.json / .md")


if __name__ == "__main__":
    main()
