from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np

from qc.schema import InspectionRecord

# Same status colours as the site (qc/app/static/app.css), in BGR.
FAIL, REVIEW, NOTE, PASS = (34, 59, 218), (13, 164, 217), (166, 184, 31), (111, 130, 0)
SEV_BGR = {"high": FAIL, "medium": REVIEW, "low": NOTE}
RESULT_BGR = {"PASS": PASS, "PASS_WITH_NOTE": NOTE, "REVIEW": REVIEW, "FAIL": FAIL}
PART_BGR = (240, 242, 242)
INK = (32, 29, 29)
SEV_RANK = {"high": 0, "medium": 1, "low": 2}
FONTS = Path(__file__).parent / "app" / "static" / "fonts"


@lru_cache(maxsize=16)
def _font(weight: int, size: int):
    try:
        from PIL import ImageFont
        return ImageFont.truetype(str(FONTS / f"Figtree-{weight}.ttf"), size)
    except Exception:   # no Pillow or no font file: fall back to OpenCV text
        return None


@lru_cache(maxsize=512)
def _chip(text: str, size: int, bg: tuple, fg: tuple, weight: int = 600):
    """A rounded label rendered once with the site's font and cached: BGRA array, or None without Pillow."""
    font = _font(weight, size)
    if font is None:
        return None
    from PIL import Image, ImageDraw
    x0, y0, x1, y1 = font.getbbox(text)
    px, py = round(size * 0.55), round(size * 0.32)
    w, h = x1 - x0 + 2 * px, round(size * 1.0) + 2 * py
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=h // 2, fill=(bg[2], bg[1], bg[0], 238))
    d.text((px - x0, (h - size) / 2 - y0 * 0.15), text, font=font, fill=(fg[2], fg[1], fg[0], 255))
    a = np.asarray(im)
    return np.ascontiguousarray(a[..., [2, 1, 0, 3]])


def _paste(out: np.ndarray, sprite: np.ndarray, x: int, y: int) -> None:
    h, w = sprite.shape[:2]
    x, y = max(0, min(x, out.shape[1] - w)), max(0, min(y, out.shape[0] - h))
    roi = out[y:y + h, x:x + w]
    s = sprite[:roi.shape[0], :roi.shape[1]]
    a = s[..., 3:4].astype(np.float32) / 255.0
    roi[:] = (s[..., :3] * a + roi * (1 - a)).astype(np.uint8)


def _label(out, text, x, y, bg, fg, size, above=True) -> None:
    sprite = _chip(text, size, tuple(bg), tuple(fg))
    if sprite is None:   # OpenCV fallback
        fs = size / 30
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, fs, 1)
        x = max(0, min(int(x), out.shape[1] - tw - 6))
        y = max(th + 8, int(y))
        cv2.rectangle(out, (x, y - th - 8), (x + tw + 6, y), bg, -1)
        cv2.putText(out, text, (x + 3, y - 4), cv2.FONT_HERSHEY_SIMPLEX, fs, fg, 1, cv2.LINE_AA)
        return
    h = sprite.shape[0]
    _paste(out, sprite, int(x), int(y - h - 4 if above and y - h - 4 >= 0 else y + 4))


def _tint(out, x1, y1, x2, y2, color, alpha) -> None:
    x1, y1, x2, y2 = max(0, x1), max(0, y1), min(out.shape[1], x2), min(out.shape[0], y2)
    if x2 > x1 and y2 > y1:
        roi = out[y1:y2, x1:x2]
        roi[:] = (roi * (1 - alpha) + np.array(color, np.float32) * alpha).astype(np.uint8)


def _rrect(out, x1, y1, x2, y2, color, t) -> None:
    """Rounded rectangle outline."""
    r = int(max(2, min(14, 0.18 * min(x2 - x1, y2 - y1))))
    for a, b in (((x1 + r, y1), (x2 - r, y1)), ((x1 + r, y2), (x2 - r, y2)), ((x1, y1 + r), (x1, y2 - r)), ((x2, y1 + r), (x2, y2 - r))):
        cv2.line(out, a, b, color, t, cv2.LINE_AA)
    for (cx, cy), ang in (((x1 + r, y1 + r), 180), ((x2 - r, y1 + r), 270), ((x2 - r, y2 - r), 0), ((x1 + r, y2 - r), 90)):
        cv2.ellipse(out, (cx, cy), (r, r), ang, 0, 90, color, t, cv2.LINE_AA)


def _halo(out, d, z, k) -> None:
    """The worst finding gets a ring and a tick scale around it, so it is found at a glance."""
    x1, y1, x2, y2 = (v * z for v in d.bbox)
    w, h = x2 - x1, y2 - y1
    if min(w, h) <= 0 or max(w, h) / min(w, h) > 2.6:
        return
    c = (int((x1 + x2) / 2), int((y1 + y2) / 2))
    r = int(0.5 * np.hypot(w, h) + 10 * k)
    if r > 0.42 * min(out.shape[:2]):
        return
    color = SEV_BGR.get(d.severity, NOTE)
    layer = out.copy()
    cv2.circle(layer, c, r, color, -1, cv2.LINE_AA)
    cv2.addWeighted(layer, 0.16, out, 0.84, 0, out)
    cv2.circle(out, c, r, color, max(1, round(1.6 * k)), cv2.LINE_AA)
    ro = r + int(9 * k)
    for ang in range(0, 360, 6):   # dotted outer ring
        a = np.deg2rad(ang)
        cv2.circle(out, (int(c[0] + ro * np.cos(a)), int(c[1] + ro * np.sin(a))), max(1, round(1.1 * k)), color, -1, cv2.LINE_AA)
    for i, ang in enumerate(range(-50, 51, 10)):   # tick scale on the right
        a = np.deg2rad(ang)
        r0, r1 = ro + int(6 * k), ro + int((14 if i % 5 == 0 else 10) * k)
        cv2.line(out, (int(c[0] + r0 * np.cos(a)), int(c[1] + r0 * np.sin(a))),
                 (int(c[0] + r1 * np.cos(a)), int(c[1] + r1 * np.sin(a))), PART_BGR, max(1, round(1.2 * k)), cv2.LINE_AA)


def _defect_text(d) -> str:
    score = f"{100 * d.size:.0f}%" if d.size_unit == "part_frac" else f"{d.confidence:.2f}"
    text = f"{d.defect.replace('_', ' ')} {score}" + (" · check" if d.needs_review else "")
    return f"{d.part.capitalize()} · {text}" if getattr(d, "part", None) else text.capitalize()


def draw(image: np.ndarray, rec: InspectionRecord, fps: float | None = None, live: bool = False,
         banner: bool = False, labels: bool = True, max_width: int = 0) -> np.ndarray:
    """Findings drawn on a copy of the image; lines and labels scale with the image so they read the same at any size."""
    z = min(1.0, max_width / image.shape[1]) if max_width else 1.0
    out = cv2.resize(image, None, fx=z, fy=z, interpolation=cv2.INTER_AREA if z < 0.5 else cv2.INTER_LINEAR) if z < 1 else image.copy()
    if out.ndim == 2:
        out = cv2.cvtColor(out, cv2.COLOR_GRAY2BGR)
    k = max(0.6, out.shape[1] / 1280)
    lw = max(1, round(1.6 * k))
    for p in rec.parts:
        poly = (np.asarray(p.get("poly") or [], np.float32) * z).astype(np.int32).reshape(-1, 1, 2)
        if len(poly) >= 3:
            cv2.polylines(out, [poly], True, INK, lw + 2, cv2.LINE_AA)
            cv2.polylines(out, [poly], True, PART_BGR, lw, cv2.LINE_AA)
    dets = sorted(rec.detections, key=lambda d: (SEV_RANK.get(d.severity, 3), -d.size))
    if dets and labels:
        _halo(out, dets[0], z, k)
    for d in reversed(dets):   # worst drawn last, on top
        x1, y1, x2, y2 = (int(v * z) for v in d.bbox)
        color = SEV_BGR.get(d.severity, NOTE)
        _tint(out, x1, y1, x2, y2, color, 0.14)
        _rrect(out, x1, y1, x2, y2, INK, lw + 2)
        _rrect(out, x1, y1, x2, y2, color, lw)
    if labels:
        flagged = {getattr(d, "part", None) for d in dets}
        for p in rec.parts:
            if p["id"] in flagged:   # its defect label names the part
                continue
            _label(out, p["id"].capitalize(), p["bbox"][0] * z, p["bbox"][1] * z, PART_BGR, INK, round(13 * k))
        for d in reversed(dets):
            x1, y1 = int(d.bbox[0] * z), int(d.bbox[1] * z)
            color = SEV_BGR.get(d.severity, NOTE)
            _label(out, _defect_text(d), x1, y1, color, INK if d.severity == "medium" else (255, 255, 255), round(15 * k))
    if banner:
        h = int(30 * k)
        cv2.rectangle(out, (0, 0), (out.shape[1], h), RESULT_BGR.get(rec.inspection_result, (90, 90, 90)), -1)
        text = f"{rec.inspection_result.replace('_', ' ')}   {rec.unit_id or ('LIVE' if live else '')}   " \
               f"vision {rec.timings_ms.get('vision', 0):.1f} ms"
        if fps:
            text += f"   {fps:.1f} FPS"
        cv2.putText(out, text, (int(8 * k), int(21 * k)), cv2.FONT_HERSHEY_SIMPLEX, 0.6 * k, (255, 255, 255), max(1, round(k)), cv2.LINE_AA)
    return out
