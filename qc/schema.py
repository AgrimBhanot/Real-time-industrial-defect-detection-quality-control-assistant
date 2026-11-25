"""Data contracts shared by vision, rules, advisory, storage and UI (the JSON hand-off)."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Optional

SEVERITIES = ("low", "medium", "high")
RESULTS = ("PASS", "PASS_WITH_NOTE", "REVIEW", "FAIL")
ADVICE_KEYS = ("summary", "likely_causes", "recommended_actions", "verify", "log_entry")


@dataclass
class Detection:
    defect: str
    confidence: float
    bbox: list  # [x1, y1, x2, y2] in pixels
    size: float = 0.0
    size_unit: str = ""
    zone: str = ""
    severity: str = ""
    needs_review: bool = False
    part: str = ""  # tray inspection: which part the defect is on, e.g. "washer 2"

    @property
    def area_px(self) -> float:
        x1, y1, x2, y2 = self.bbox
        return max(0.0, x2 - x1) * max(0.0, y2 - y1)


@dataclass
class InspectionRecord:
    unit_id: str
    timestamp: str
    source: str
    image_ref: str
    image_size: list  # [w, h]
    detections: list = field(default_factory=list)
    inspection_result: str = "PASS"
    rule_trace: list = field(default_factory=list)
    context: dict = field(default_factory=dict)
    timings_ms: dict = field(default_factory=dict)
    parts: list = field(default_factory=list)   # tray inspection: [{id, type, confidence, bbox}]
    gt_result: Optional[str] = None             # verdict the same rules give the dataset's own labels, if labelled
    gt_defects: list = field(default_factory=list)

    @property
    def part_counts(self) -> dict:
        out: dict = {}
        for p in self.parts:
            out[p["type"]] = out.get(p["type"], 0) + 1
        return out

    @property
    def gt_outcome(self) -> Optional[str]:
        """How the verdict compares with the labels: ok | escape (bad unit passed) | false_reject."""
        if self.gt_result is None:
            return None
        ok = ("PASS", "PASS_WITH_NOTE")
        if (self.gt_result in ok) == (self.inspection_result in ok):
            return "ok"
        return "escape" if self.inspection_result in ok else "false_reject"

    def to_dict(self) -> dict:
        return asdict(self)

    def llm_view(self) -> dict:
        """Compact, grounded record for the prompt: findings + context, no timings or paths."""
        return {
            "unit_id": self.unit_id,
            "inspection_result": self.inspection_result,
            **({"parts_on_tray": self.part_counts} if self.parts else {}),
            "detections": [
                {
                    **({"part": d.part} if d.part else {}),
                    "defect": d.defect,
                    "severity": d.severity,
                    "confidence": round(d.confidence, 2),
                    "size": round(d.size, 4),
                    "size_unit": d.size_unit,
                    "zone": d.zone,
                    "needs_review": d.needs_review,
                }
                for d in self.detections
            ],
            "rule_trace": self.rule_trace,
            "context": self.context,
        }

    def llm_view_compact(self) -> dict:
        """Same facts, fewer tokens: one entry per (defect, severity), most severe first; no rule trace."""
        groups: dict = {}
        for d in self.detections:
            g = groups.setdefault((d.defect, d.severity), {
                "defect": d.defect, "severity": d.severity, "count": 0, "zones": [], "max_size": 0.0,
                "size_unit": d.size_unit, "needs_review": 0})
            g["count"] += 1
            g["needs_review"] += bool(d.needs_review)
            g["max_size"] = max(g["max_size"], round(d.size, 3))
            if d.zone not in g["zones"]:
                g["zones"].append(d.zone)
        order = sorted(groups.values(), key=lambda g: -SEVERITIES.index(g["severity"]))
        return {"unit_id": self.unit_id, "inspection_result": self.inspection_result,
                "detections": order, "context": self.context}

    @property
    def defect_classes(self) -> list:
        return sorted({d.defect for d in self.detections})


@dataclass
class AdviceResult:
    unit_id: str
    advice: dict
    backend: str
    valid: bool
    fallback: bool
    attempts: int = 1
    errors: list = field(default_factory=list)
    ttft_ms: Optional[float] = None
    tok_s: Optional[float] = None
    total_ms: Optional[float] = None
    load_ms: Optional[float] = None
    prompt_tokens: Optional[int] = None
    generated_tokens: Optional[int] = None
    repaired: bool = False             # truncated output repaired (loop collapsed / JSON closed), then validated
    cached_tokens: Optional[int] = None  # prompt tokens reused from the previous prompt (KV prefix cache)
    loop_stop: bool = False            # the server stopped generation because the output was repeating
    queue_ms: Optional[float] = None   # waiting behind other units in the advisory queue
    e2e_ms: Optional[float] = None     # frame captured -> validated advice ready (shown in the UI)
    raw: str = ""

    def to_dict(self) -> dict:
        return asdict(self)
