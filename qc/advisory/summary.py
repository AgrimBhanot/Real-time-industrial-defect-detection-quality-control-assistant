"""Shift summary: Llama reads aggregate log statistics and points at likely process drift."""
from __future__ import annotations

import json

from qc.advisory.llm import ExecuTorchLLM
from qc.advisory.prompt import llama3_chat, sop_notes
from qc.advisory.validator import extract_json, mentioned_classes
from qc.storage import InspectionDB

SYSTEM = (
    "You are a QC shift assistant for a {title} line. You receive aggregate inspection statistics as JSON. "
    'Reply with ONLY a JSON object with keys "trend" (one sentence), "likely_process_issue" (one sentence '
    'based on the SOP notes) and "actions" (list of 1-3 short strings). Mention only defect types that '
    "appear in the statistics. Do not invent numbers."
)
KEYS = ("trend", "likely_process_issue", "actions")


def _template(profile: dict, stats: dict) -> dict:
    units = stats["units"] or 1
    fails = stats["results"].get("FAIL", 0)
    top, n = next(iter(stats["defects"].items()))
    sop = profile.get("sop", {}).get(top, {})
    return {
        "trend": f"{fails}/{units} units failed ({100 * fails / units:.0f}%); most frequent defect: {top} ({n}).",
        "likely_process_issue": f"Repeated {top}: check {', '.join(sop.get('causes', ['the process'])[:2])}.",
        "actions": sop.get("actions", ["escalate to process engineer"])[:3],
    }


def shift_summary(profile: dict, db: InspectionDB, llm=None, last_n: int = 200) -> dict:
    stats = db.stats(last_n, profile.get("name"))
    if not stats["defects"]:
        return {"trend": f"No defects in the last {stats['units']} units.", "likely_process_issue": "none",
                "actions": ["continue monitoring"], "backend": "template", "stats": stats}
    if isinstance(llm, ExecuTorchLLM):
        top = list(stats["defects"])[:3]
        prompt = llama3_chat([
            ("system", SYSTEM.format(title=profile.get("title", profile["name"]))),
            ("user", f"SOP NOTES:\n{sop_notes(profile, top)}\n\nSTATISTICS:\n{json.dumps(stats)}"),
        ])
        try:
            out = llm.complete(prompt)
            obj = extract_json(out.text)
            blob = json.dumps(obj) if obj else ""
            if obj and all(k in obj for k in KEYS) and mentioned_classes(blob, profile) <= set(stats["defects"]):
                return {**{k: obj[k] for k in KEYS}, "backend": "executorch", "stats": stats, "llm": out.stats}
        except Exception as exc:
            return {**_template(profile, stats), "backend": "template", "fallback_reason": str(exc), "stats": stats}
    return {**_template(profile, stats), "backend": "template", "stats": stats}
