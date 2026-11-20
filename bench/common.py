from __future__ import annotations

import numpy as np

from qc.config import Config
from qc.rules import RuleEngine
from qc.schema import InspectionRecord
from qc.sources import FolderSource
from qc.vision.detector import GroundTruthDetector


def stats(values: list) -> dict:
    if not values:
        return {}
    a = np.asarray(values, dtype=float)
    return {"mean": float(a.mean()), "p50": float(np.percentile(a, 50)), "p95": float(np.percentile(a, 95)),
            "min": float(a.min()), "max": float(a.max()), "n": int(a.size)}


def sample_records(cfg: Config, n: int = 30, seed: int = 0) -> list[InspectionRecord]:
    """Realistic advisory inputs: ground-truth findings from the demo set, run through the real rule engine."""
    src = FolderSource(cfg.path(cfg.section("source")["path"]), shuffle=True, loop=False, seed=seed)
    gt, rules, out = GroundTruthDetector(cfg.profile["classes"]), RuleEngine(cfg.profile), []
    for f in src:
        dets, _ = gt.detect(f)
        if not dets:
            continue
        h, w = f.image.shape[:2]
        trace = rules.annotate(dets, w, h)
        result, why = rules.decide(dets)
        out.append(InspectionRecord(f"U-BENCH-{len(out):04d}", "bench", "bench", f.ref, [w, h], dets, result,
                                    trace + why, {"station": cfg.profile.get("station"), "recent_units": 50,
                                                  "recent_fail": 5, "recent_defects": {dets[0].defect: 3}}))
        if len(out) >= n:
            break
    if not out:
        raise RuntimeError("no labelled defective images in the demo set; run training/prepare_deeppcb.py first")
    return out
