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

    def to_dict(self) -> dict:
        return asdict(self)

    def llm_view(self) -> dict:
        """Compact, grounded record for the prompt: findings + context, no timings or paths."""
        return {
            "unit_id": self.unit_id,
            "inspection_result": self.inspection_result,
            "detections": [
                {
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
    loop_stop: bool = False            # the server stopped generation because the output was repeating
    queue_ms: Optional[float] = None   # waiting behind other units in the advisory queue
    e2e_ms: Optional[float] = None     # frame captured -> validated advice ready (shown in the UI)
    raw: str = ""

    def to_dict(self) -> dict:
        return asdict(self)
