"""File naming for captures: <part>__<condition>__<time>.jpg, so a physical part is traceable to every photo."""
from __future__ import annotations

import re

NAME = re.compile(r"^([A-Za-z0-9-]+)__([a-z_]+?)__(.+)$")
PART = re.compile(r"^[A-Za-z0-9-]+$")


def check_part(part: str) -> str:
    if not PART.match(part):
        raise ValueError(f"part id {part!r}: use letters, digits and '-' only (e.g. B017)")
    return part


def parse_name(stem: str) -> tuple[str, str]:
    m = NAME.match(stem)
    if not m:
        raise ValueError(f"{stem}: expected <part>__<condition>__<time>")
    return m.group(1), m.group(2)
