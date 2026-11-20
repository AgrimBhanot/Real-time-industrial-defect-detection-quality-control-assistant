"""Grounded prompts: Llama sees structured findings + SOP notes for those classes + recent context, never pixels."""
from __future__ import annotations

import json

from qc.schema import InspectionRecord

SYSTEM = (
    "You are a quality-control assistant on a {title} line (station {station}). "
    "You receive ONE inspection record as JSON. The PASS/FAIL/REVIEW decision was already made by a "
    "deterministic rule engine; never change or question it.\n"
    "Reply with ONLY a JSON object with exactly these keys:\n"
    '"summary": one sentence, at most 25 words; "likely_causes": list of 1-3 strings, at most 8 words each; '
    '"recommended_actions": list of 1-3 strings, at most 8 words each; "verify": one check, at most 15 words; '
    '"log_entry": one line, at most 20 words, written once.\n'
    "Rules: mention ONLY defect types present in the record. With several defects, lead with the most severe "
    "and summarise the rest briefly. Take causes and actions from the SOP notes. Use the context (recent "
    "defect counts) to point out repeats. Do not invent measurements. Never repeat a phrase."
)


def sop_notes(profile: dict, classes: list[str]) -> str:
    sop = profile.get("sop", {})
    lines = []
    for c in classes:
        e = sop.get(c)
        if e:
            lines.append(f"- {c} ({e.get('meaning', '')}): causes: {'; '.join(e.get('causes', []))}. "
                         f"actions: {'; '.join(e.get('actions', []))}.")
    return "\n".join(lines) or "- (no SOP notes for these defect types)"


def user_message(profile: dict, view: dict) -> str:
    classes = sorted({d["defect"] for d in view["detections"]})
    return f"SOP NOTES:\n{sop_notes(profile, classes)}\n\nINSPECTION RECORD:\n{json.dumps(view, separators=(',', ':'))}"


def worked_example(profile: dict) -> tuple[str, str]:
    cls = profile["classes"][0]
    e = profile.get("sop", {}).get(cls, {"meaning": cls, "causes": ["unknown"], "actions": ["inspect the process"]})
    view = {
        "unit_id": "U-EXAMPLE",
        "inspection_result": "FAIL",
        "detections": [{"defect": cls, "severity": "high", "confidence": 0.91, "size": 0.05,
                        "size_unit": "mm2", "zone": "B2", "needs_review": False}],
        "rule_trace": [f"{cls} -> high (base)", "FAIL: 1 high-severity defect(s)"],
        "context": {"station": profile.get("station", ""), "recent_units": 50, "recent_fail": 4,
                    "recent_defects": {cls: 3}},
    }
    answer = {
        "summary": f"Unit failed with one high-severity {cls} ({e.get('meaning', cls)}) in zone B2.",
        "likely_causes": e["causes"][:2],
        "recommended_actions": e["actions"][:2],
        "verify": f"Re-inspect the next 5 units for {cls} after the correction.",
        "log_entry": f"U-EXAMPLE FAIL {cls}/high B2; 3rd {cls} in last 50 units; {e['actions'][0]}.",
    }
    return user_message(profile, view), json.dumps(answer)


def build_messages(record: InspectionRecord, profile: dict) -> list[tuple[str, str]]:
    ex_user, ex_answer = worked_example(profile)
    return [
        ("system", SYSTEM.format(title=profile.get("title", profile["name"]), station=profile.get("station", ""))),
        ("user", ex_user),
        ("assistant", ex_answer),
        ("user", user_message(profile, record.llm_view())),
    ]


def llama3_chat(messages: list[tuple[str, str]], bos: bool = True) -> str:
    """Llama 3.x chat template. The ExecuTorch runners encode with num_bos=0, so BOS is written here."""
    out = "<|begin_of_text|>" if bos else ""
    for role, content in messages:
        out += f"<|start_header_id|>{role}<|end_header_id|>\n\n{content}<|eot_id|>"
    return out + "<|start_header_id|>assistant<|end_header_id|>\n\n"
