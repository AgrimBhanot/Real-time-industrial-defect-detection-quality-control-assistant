"""Deterministic severity + PASS/FAIL policy. Severity depends on type, size and location, never on confidence."""
from __future__ import annotations

import string

from qc.schema import SEVERITIES, Detection


def _bump(level: str) -> str:
    return SEVERITIES[min(len(SEVERITIES) - 1, SEVERITIES.index(level) + 1)]


class RuleEngine:
    def __init__(self, profile: dict):
        sev = profile["severity"]
        self.class_rules: dict = sev["classes"]
        self.thresholds: dict = sev.get("size_thresholds", {}) or {}
        self.review_below = float(sev.get("confidence_review_below", 0.0))
        self.px_per_mm = profile.get("px_per_mm")
        zones = profile.get("zones") or {"rows": 3, "cols": 3}
        self.rows, self.cols = int(zones["rows"]), int(zones["cols"])
        dec = profile["decision"]
        self.fail_if_any = dec.get("fail_if_any", "high")
        self.fail_medium = int(dec.get("fail_if_medium_count_at_least", 2))
        self.review_medium = int(dec.get("review_if_medium_count_at_least", 1))

    @property
    def size_unit(self) -> str:
        return "mm2" if self.px_per_mm else "frame_frac"

    def measure(self, det: Detection, w: int, h: int) -> float:
        if self.px_per_mm:
            return det.area_px / float(self.px_per_mm) ** 2
        return det.area_px / float(w * h)

    def zone(self, det: Detection, w: int, h: int) -> str:
        x1, y1, x2, y2 = det.bbox
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        row = min(self.rows - 1, max(0, int(cy / h * self.rows)))
        col = min(self.cols - 1, max(0, int(cx / w * self.cols)))
        return f"{string.ascii_uppercase[row]}{col + 1}"

    def severity(self, defect: str, size: float) -> tuple[str, str]:
        rule = self.class_rules.get(defect)
        if rule is None:
            return "medium", f"{defect}: not in policy -> medium (default)"
        base = rule["base"]
        mode = rule.get("size_rule")
        thr = self.thresholds.get(defect)
        if mode and thr:
            lo, hi = float(thr[0]), float(thr[1])
            if mode == "three_level":
                if size >= hi:
                    return "high", f"{defect}: size {size:.4g} >= P66 {hi:.4g} -> high"
                if size <= lo:
                    return "low", f"{defect}: size {size:.4g} <= P33 {lo:.4g} -> low"
            elif mode == "escalate_only" and size >= hi:
                up = _bump(base)
                return up, f"{defect}: size {size:.4g} >= P66 {hi:.4g} -> {up}"
        return base, f"{defect} -> {base} (base)"

    def annotate(self, dets: list[Detection], w: int, h: int) -> list[str]:
        trace = []
        for d in dets:
            d.size = self.measure(d, w, h)
            d.size_unit = self.size_unit
            d.zone = self.zone(d, w, h)
            d.severity, why = self.severity(d.defect, d.size)
            d.needs_review = d.confidence < self.review_below or d.defect == "anomaly"
            if d.defect == "anomaly":
                why = "anomaly: unlike the good parts, cause not identified [human review]"
            elif d.needs_review:
                why += f" [conf {d.confidence:.2f} < {self.review_below:.2f}: human review]"
            trace.append(why)
        return trace

    def decide(self, dets: list[Detection]) -> tuple[str, list[str]]:
        confident = [d for d in dets if not d.needs_review]
        n_review = len(dets) - len(confident)
        sevs = [d.severity for d in confident]
        n_med = sevs.count("medium")
        if self.fail_if_any in sevs:
            result, why = "FAIL", f"FAIL: {sevs.count(self.fail_if_any)} {self.fail_if_any}-severity defect(s)"
        elif n_med >= self.fail_medium:
            result, why = "FAIL", f"FAIL (rework): {n_med} medium defects >= {self.fail_medium}"
        elif n_med >= self.review_medium:
            result, why = "REVIEW", f"REVIEW: {n_med} medium defect(s)"
        elif sevs:
            result, why = "PASS_WITH_NOTE", f"PASS with note: {len(sevs)} low-severity defect(s)"
        else:
            result, why = "PASS", "PASS: no confident defects"
        if n_review and result in ("PASS", "PASS_WITH_NOTE"):
            result, why = "REVIEW", why + f"; {n_review} low-confidence detection(s) need human review"
        return result, [why]
