"""Checks that Llama output is well-formed JSON and grounded (mentions no defect absent from the record)."""
from __future__ import annotations

import json
import re
from typing import Optional

from qc.schema import ADVICE_KEYS, InspectionRecord

MAX_FIELD_CHARS = 300
LIST_KEYS = ("likely_causes", "recommended_actions")


def extract_json(text: str) -> Optional[dict]:
    """First balanced, parseable JSON object in text (tolerates chatter before/after)."""
    start = text.find("{")
    while start != -1:
        depth, in_str, esc = 0, False, False
        for j in range(start, len(text)):
            ch = text[j]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
            elif ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        obj = json.loads(text[start:j + 1])
                        if isinstance(obj, dict):
                            return obj
                    except json.JSONDecodeError:
                        pass
                    break
        start = text.find("{", start + 1)
    return None


def collapse_trailing_loop(s: str, min_p: int = 8, max_p: int = 80) -> tuple[str, bool]:
    """If s ends in a span repeated back-to-back (a generation loop, possibly cut mid-copy), keep one copy."""
    n, best = len(s), None
    for p in range(min_p, min(max_p, n // 2) + 1):
        r, i = 0, n - 1
        while i - p >= 0 and s[i] == s[i - p]:
            r, i = r + 1, i - 1
        if r >= p and (best is None or r > best[1]):
            best = (p, r)
    if not best:
        return s, False
    p, r = best
    cut = n - r  # s[:cut] holds the text before the loop plus one period (possibly rotated mid-word)
    end = cut
    while end < n and end - cut < p and not s[end].isspace() and s[end] not in '",;':
        end += 1  # finish the word the period boundary fell into
    return s[:end].rstrip(" ;,"), True


def _close(fragment: str) -> str:
    """Close an unterminated string / arrays / objects at the end of a JSON fragment."""
    stack, in_str, esc = [], False, False
    for ch in fragment:
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch in "{[":
            stack.append("}" if ch == "{" else "]")
        elif ch in "}]" and stack:
            stack.pop()
    out = fragment.rstrip("\\") + '"' if in_str else fragment.rstrip().rstrip(",:")
    return out + "".join(reversed(stack))


def repair_json(text: str) -> tuple[Optional[dict], list[str]]:
    """Recover a JSON object from output that was cut off (token limit or loop stop). Returns (obj, notes)."""
    start = text.find("{")
    if start < 0:
        return None, []
    frag, looped = collapse_trailing_loop(text[start:].rstrip())
    notes = ["collapsed a repetition loop"] if looped else []
    for _ in range(6):
        try:
            obj = json.loads(_close(frag))
            if isinstance(obj, dict):
                return obj, notes + ["closed truncated JSON"]
        except json.JSONDecodeError:
            pass
        cut = frag.rfind(",")  # drop the last (partial) element and retry
        if cut <= 0:
            break
        frag = frag[:cut]
    return None, notes


def _patterns(profile: dict, cls: str) -> list[re.Pattern]:
    phrases = profile.get("mention_patterns", {}).get(cls) or [cls, cls.replace("_", " "), cls.replace("-", " ")]
    return [re.compile(rf"(?<![\w-]){re.escape(p)}(?![\w-])", re.IGNORECASE) for p in set(phrases)]


def mentioned_classes(text: str, profile: dict) -> set[str]:
    return {c for c in profile["classes"] if any(p.search(text) for p in _patterns(profile, c))}


_LEAD = re.compile(r"^\W*(?:the\s+)?(?:unit|part|tray|board|sheet|it)?\s*(?:\S+\s+)?(?:has\s+|is\s+)?"
                   r"(?:fail(?:ed|s)?|pass(?:ed|es)?|review)\b(?:\s+(?:with\s+note|inspection))?(?:\s+(?:with|due to|because of))?\W*",
                   re.IGNORECASE)


def verdict_conflict(text: str, result: str) -> bool:
    """True when the text states a verdict other than the rule engine's."""
    said = set()
    if re.search(r"\b(?:unit|part|tray|board|sheet|it|inspection)\s+(?:\S+\s+)?(?:has\s+)?fail(?:ed|s)\b", text, re.I) \
            or re.match(r"\W*fail(?:ed)?\b", text, re.I) or re.search(r"\bFAIL\b", text):
        said.add("FAIL")
    if re.search(r"\b(?:unit|part|tray|board|sheet|it|inspection)\s+(?:\S+\s+)?(?:has\s+)?pass(?:ed|es)\b", text, re.I) \
            or re.match(r"\W*pass(?:ed)?\b", text, re.I) or re.search(r"\bPASS(?:_WITH_NOTE)?\b", text):
        said.add("PASS")
    if re.match(r"\W*review\b", text, re.I) or re.search(r"\bREVIEW\b", text):
        said.add("REVIEW")
    return bool(said - {"PASS" if result.startswith("PASS") else result})


def _fix_verdict(advice: dict, record: InspectionRecord, profile: dict, notes: Optional[list]) -> list[str]:
    """A wrong verdict is an error (strict) or is corrected from the record and noted (repair mode)."""
    result = record.inspection_result
    for k in ("summary", "log_entry"):
        if not verdict_conflict(advice[k], result):
            continue
        if notes is None:
            return [f"{k} states a verdict other than {result}"]
        if k == "summary":
            rest = _LEAD.sub("", advice[k], count=1).strip()
            if not rest or verdict_conflict(rest, result):
                worst = record.detections[0] if record.detections else None
                rest = f"{worst.defect} in zone {worst.zone}." if worst else "see findings."
            advice[k] = f"{result}: {rest}"
        else:
            advice[k] = re.sub(r"\b(?:FAIL(?:ED)?|PASS(?:ED|_WITH_NOTE)?|REVIEW)\b", result, advice[k], flags=re.I)
        notes.append(f"verdict corrected in {k}")
    label = result.replace("_", " ")
    if not re.match(rf"\W*(?:{result}|{label})\b", advice["summary"], re.I):
        rest = _LEAD.sub("", advice["summary"], count=1).strip() or advice["summary"]
        advice["summary"] = f"{result}: {rest}"  # formatting only: same verdict, uniform lead
    return []


def _drop_name_causes(advice: dict, record: InspectionRecord, profile: dict, notes: Optional[list]) -> None:
    """A defect's own name is not a cause: replace it with the SOP's causes for the units' defects."""
    names = {c.replace("_", " ").replace("-", " ").lower() for c in profile["classes"]}
    keep = [c for c in advice["likely_causes"] if c.strip(". ").replace("_", " ").replace("-", " ").lower() not in names]
    if len(keep) == len(advice["likely_causes"]) or notes is None:
        return
    for c in record.defect_classes:
        keep += [x for x in profile.get("sop", {}).get(c, {}).get("causes", []) if x not in keep]
    advice["likely_causes"] = keep[:3] or ["not in SOP table"]
    notes.append("defect name used as cause: replaced from the SOP")


_COUNT_CLAIM = re.compile(r"\b(?:in|of|over)\s+(?:the\s+)?(?:last|past|recent)\s+(\d+)\s+units?\b", re.IGNORECASE)
_ORDINAL = re.compile(r"\b(\d+)(?:st|nd|rd|th)\b", re.IGNORECASE)


def _fix_claims(advice: dict, record: InspectionRecord, profile: dict, notes: Optional[list]) -> list[str]:
    """Counts must come from the record's context, and `verify` must be a check, not a copy of the log line."""
    ctx = record.context or {}
    allowed = set((ctx.get("recent_defects") or {}).values()) | {ctx.get("recent_fail")}
    allowed |= {n + 1 for n in allowed if isinstance(n, int)}  # "3rd" may count this unit too
    for k in ("summary", "verify", "log_entry"):
        keep, dropped = [], False
        for clause in advice[k].split(";"):
            m = _COUNT_CLAIM.search(clause)
            ords = [int(x) for x in _ORDINAL.findall(clause)]
            if m and (int(m.group(1)) != ctx.get("recent_units") or any(o not in allowed for o in ords)):
                dropped = True
            else:
                keep.append(clause.strip())
        if dropped:
            if notes is None:
                return [f"{k} states a count that is not in the record"]
            advice[k] = "; ".join(c for c in keep if c).rstrip(".; ") + "." if any(keep) else ""
            notes.append(f"unsupported count removed from {k}")
    worst = max(record.detections, key=lambda d: ("low", "medium", "high").index(d.severity or "low"), default=None)
    name = worst.defect.replace("_", " ") if worst else "defects"
    if not advice["verify"] or (record.unit_id and record.unit_id in advice["verify"]):
        if notes is None:
            return ["'verify' is not a check"]
        advice["verify"] = f"Re-inspect the next 5 units for {name}."
        notes.append("'verify' replaced: it was not a check")
    if not advice["summary"]:
        advice["summary"] = f"{name} in zone {worst.zone}." if worst else "see findings."
    if not advice["log_entry"]:
        advice["log_entry"] = f"{record.unit_id} {record.inspection_result} {name}."
    return []


def validate(text: str, record: InspectionRecord, profile: dict,
             notes: Optional[list] = None) -> tuple[Optional[dict], list[str]]:
    """Strict checks on Llama output. If `notes` is a list, truncated output is repaired (loop collapsed,
    JSON closed) and what was repaired is appended to it; the repaired object must still pass every check."""
    obj = extract_json(text)
    if obj is None and notes is not None:
        obj, how = repair_json(text)
        if obj is not None:
            notes += how
    if obj is None:
        return None, ["no parseable JSON object in output"]
    errors = []
    advice = {}
    for k in ADVICE_KEYS:
        if k not in obj:
            errors.append(f"missing key {k!r}")
            continue
        v = obj[k]
        if k in LIST_KEYS:
            if isinstance(v, str):
                v = [v]
            if not isinstance(v, list) or not v or not all(isinstance(x, str) and x.strip() for x in v):
                errors.append(f"{k!r} must be a non-empty list of strings")
                continue
            v = [x.strip()[:MAX_FIELD_CHARS] for x in v[:4]]
        else:
            if not isinstance(v, str) or not v.strip():
                errors.append(f"{k!r} must be a non-empty string")
                continue
            if len(v) > MAX_FIELD_CHARS:
                errors.append(f"{k!r} longer than {MAX_FIELD_CHARS} chars")
                continue
            v = v.strip()
        advice[k] = v
    if errors:
        return None, errors
    blob = " ".join(x if isinstance(x, str) else " ".join(x) for x in advice.values())
    invented = mentioned_classes(blob, profile) - set(record.defect_classes)
    if invented:
        return None, [f"mentions defect(s) not in record: {sorted(invented)}"]
    errors = _fix_claims(advice, record, profile, notes) or _fix_verdict(advice, record, profile, notes)
    if errors:
        return None, errors
    _drop_name_causes(advice, record, profile, notes)
    return advice, []
