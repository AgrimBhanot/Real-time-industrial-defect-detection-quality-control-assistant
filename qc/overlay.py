from __future__ import annotations

import cv2
import numpy as np

from qc.schema import InspectionRecord

SEV_BGR = {"low": (80, 200, 80), "medium": (0, 170, 255), "high": (40, 40, 230)}
RESULT_BGR = {"PASS": (60, 150, 60), "PASS_WITH_NOTE": (60, 150, 60), "REVIEW": (0, 140, 210), "FAIL": (40, 40, 210)}
PART_BGR = (235, 190, 90)


def draw(image: np.ndarray, rec: InspectionRecord, fps: float | None = None, live: bool = False,
         banner: bool = True, labels: bool = True, max_width: int = 0) -> np.ndarray:
    """Boxes on a copy of the image; lines and text scale with the image so they read the same at any size."""
    z = min(1.0, max_width / image.shape[1]) if max_width else 1.0
    out = cv2.resize(image, None, fx=z, fy=z, interpolation=cv2.INTER_AREA if z < 0.5 else cv2.INTER_LINEAR) if z < 1 else image.copy()
    if out.ndim == 2:
        out = cv2.cvtColor(out, cv2.COLOR_GRAY2BGR)
    k = max(0.75, out.shape[1] / 1100)
    lw, fs, ft = max(1, round(2 * k)), 0.5 * k, max(1, round(1.2 * k))
    for p in rec.parts:
        poly = (np.asarray(p.get("poly") or [], np.float32) * z).astype(np.int32).reshape(-1, 1, 2)
        if len(poly) >= 3:
            cv2.polylines(out, [poly], True, PART_BGR, lw, cv2.LINE_AA)
        if not labels:
            continue
        x1, y1 = p["bbox"][0] * z, p["bbox"][1] * z
        _label(out, p["id"], x1, y1, PART_BGR, fs * 0.85, ft, (20, 20, 20))
    for d in rec.detections:
        x1, y1, x2, y2 = (int(v * z) for v in d.bbox)
        color = SEV_BGR.get(d.severity, (200, 200, 200))
        cv2.rectangle(out, (x1, y1), (x2, y2), color, lw + 1, cv2.LINE_AA)
        if not labels:
            continue
        score = f"{100 * d.size:.0f}%" if d.size_unit == "part_frac" else f"{d.confidence:.2f}"
        _label(out, f"{d.defect.replace('_', ' ')} {score}" + (" ?" if d.needs_review else ""), x1, y1, color, fs, ft,
               (20, 20, 20) if d.severity == "medium" else (255, 255, 255))
    if banner:
        h = int(30 * k)
        cv2.rectangle(out, (0, 0), (out.shape[1], h), RESULT_BGR.get(rec.inspection_result, (90, 90, 90)), -1)
        text = f"{rec.inspection_result.replace('_', ' ')}   {rec.unit_id or ('LIVE' if live else '')}   " \
               f"vision {rec.timings_ms.get('vision', 0):.1f} ms"
        if fps:
            text += f"   {fps:.1f} FPS"
        cv2.putText(out, text, (int(8 * k), int(21 * k)), cv2.FONT_HERSHEY_SIMPLEX, 0.6 * k, (255, 255, 255), ft, cv2.LINE_AA)
    return out


def _label(out, text, x, y, color, fs, ft, ink) -> None:
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, fs, ft)
    x = max(0, min(int(x), out.shape[1] - tw - 4))
    y = max(th + 6, int(y))
    cv2.rectangle(out, (x, y - th - 6), (x + tw + 4, y), color, -1)
    cv2.putText(out, text, (x + 2, y - 4), cv2.FONT_HERSHEY_SIMPLEX, fs, ink, ft, cv2.LINE_AA)
