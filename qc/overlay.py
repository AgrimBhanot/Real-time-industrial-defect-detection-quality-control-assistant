from __future__ import annotations

import cv2
import numpy as np

from qc.schema import InspectionRecord

SEV_BGR = {"low": (80, 200, 80), "medium": (0, 170, 255), "high": (40, 40, 230)}
RESULT_BGR = {"PASS": (60, 170, 60), "PASS_WITH_NOTE": (60, 170, 60), "REVIEW": (0, 160, 230), "FAIL": (40, 40, 210)}


def draw(image: np.ndarray, rec: InspectionRecord, fps: float | None = None) -> np.ndarray:
    out = image.copy()
    for d in rec.detections:
        x1, y1, x2, y2 = (int(v) for v in d.bbox)
        color = SEV_BGR.get(d.severity, (200, 200, 200))
        cv2.rectangle(out, (x1, y1), (x2, y2), color, 2, cv2.LINE_AA if not d.needs_review else cv2.LINE_4)
        label = f"{d.defect} {d.severity[:1].upper()} {d.confidence:.2f}" + (" ?" if d.needs_review else "")
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
        ty = max(th + 4, y1)
        cv2.rectangle(out, (x1, ty - th - 4), (x1 + tw + 4, ty), color, -1)
        cv2.putText(out, label, (x1 + 2, ty - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
    badge = rec.inspection_result.replace("_", " ")
    cv2.rectangle(out, (0, 0), (out.shape[1], 30), RESULT_BGR.get(rec.inspection_result, (90, 90, 90)), -1)
    text = f"{rec.unit_id}  {badge}  vision {rec.timings_ms.get('vision', 0):.1f} ms"
    if fps:
        text += f"  {fps:.1f} FPS"
    cv2.putText(out, text, (8, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
    return out
