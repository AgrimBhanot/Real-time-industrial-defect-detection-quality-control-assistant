"""Score the detector LIVE on physical parts whose true condition you type in.

  python training/live_test.py --backend tensorrt

Parts used for training or validation are refused (groups.json). Reports, with counts: defective parts missed (no
confident defect found), defective parts with the right defect type, good parts not passed. Writes
bench/results/live_<profile>_*.json and keeps every photo under runs/live/.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from qc.config import load_config  # noqa: E402
from qc.rules import RuleEngine  # noqa: E402
from qc.sources import CameraSource, Frame  # noqa: E402
from qc.vision import build_detector  # noqa: E402
from training.capture_images import add_camera_args, ask_part, grab  # noqa: E402


def summarise(rows: list[dict]) -> dict:
    bad = [r for r in rows if r["truth"] != "good"]
    good = [r for r in rows if r["truth"] == "good"]
    return {
        "views": len(rows), "parts": len({r["part"] for r in rows}),
        "defective_views": len(bad), "defect_missed": sum(not r["found"] for r in bad),
        "right_type_found": sum(r["truth"] in r["found"] for r in bad),
        "defective_verdict_pass": sum(r["verdict"] == "PASS" for r in bad),
        "good_views": len(good), "good_not_passed": sum(r["verdict"] not in ("PASS", "PASS_WITH_NOTE") for r in good),
        "good_with_any_detection": sum(bool(r["found"]) for r in good),
    }


def used_for_training(profile: str) -> set:
    f = ROOT / f"data/datasets/{profile}/groups.json"
    if not f.exists():
        return set()
    g = json.loads(f.read_text())
    return set(g["train_groups"]) | set(g["val_groups"])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_camera_args(ap)
    ap.add_argument("--backend", default="tensorrt")
    ap.add_argument("--set", action="append", default=[])
    a = ap.parse_args()
    cfg = load_config(overrides=[f"profile={a.profile}", f"vision.backend={a.backend}", *a.set])
    seen = used_for_training(a.profile)
    if not seen:
        print("WARNING: no groups.json here, so training parts cannot be refused; use only new parts.")
    det, rules = build_detector(cfg), RuleEngine(cfg.profile)
    det.warmup()
    cap = CameraSource(a.kind, a.index, a.width, a.height)._open()
    stamp = datetime.now().strftime("%m%d_%H%M%S")
    shots = ROOT / f"runs/live/{stamp}"
    shots.mkdir(parents=True, exist_ok=True)
    rows = []
    try:
        while (pc := ask_part(cfg.profile["classes"])) is not None:
            part, truth = pc
            if part in seen:
                print(f"  {part} was used in training/validation: not scored")
                continue
            img = grab(cap, a.crop)
            dets, t = det.detect(Frame(img, part, "live"))
            h, w = img.shape[:2]
            rules.annotate(dets, w, h)
            verdict, _ = rules.decide(dets)
            found = sorted({d.defect for d in dets if not d.needs_review})
            rows.append({"part": part, "truth": truth, "verdict": verdict, "found": found,
                         "low_confidence": sorted({d.defect for d in dets if d.needs_review}), "ms": t})
            cv2.imwrite(str(shots / f"{len(rows):04d}_{part}__{truth}.jpg"), img)
            print(f"  {verdict}  found: {', '.join(found) or '-'}  (truth: {truth})")
    finally:
        cap.release()
        if rows:
            out = ROOT / f"bench/results/live_{a.profile}_{stamp}.json"
            out.write_text(json.dumps({"backend": det.backend, "camera": vars(a), "summary": summarise(rows),
                                       "rows": rows}, indent=1))
            print(json.dumps(summarise(rows), indent=1), f"\nwrote {out}")


if __name__ == "__main__":
    main()
