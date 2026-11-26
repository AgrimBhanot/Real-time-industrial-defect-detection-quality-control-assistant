import json

import pytest

from qc.advisory.llm import TemplateLLM, parse_observer
from qc.advisory.prompt import build_messages, llama3_chat
from qc.advisory.validator import extract_json, validate


GOOD = {"summary": "Unit failed with a high-severity open circuit in zone A1.",
        "likely_causes": ["over-etching"], "recommended_actions": ["check etch time"],
        "verify": "re-inspect next 5 units", "log_entry": "U-1 FAIL open/high A1"}


def test_extract_json_with_chatter():
    text = 'Sure! Here you go:\n{"a": {"b": "x}"}, "c": 1}\nthanks'
    assert extract_json(text) == {"a": {"b": "x}"}, "c": 1}
    assert extract_json("no json here") is None
    assert extract_json('{broken {"ok": true}') == {"ok": True}


def test_validate_accepts_grounded(record, profile):
    advice, errors = validate(json.dumps(GOOD), record, profile)
    assert errors == [] and advice["summary"].startswith("FAIL: ")


def test_validate_rejects_invented_defect(record, profile):
    bad = dict(GOOD, summary="Open circuit plus a short circuit nearby.")
    advice, errors = validate(json.dumps(bad), record, profile)
    assert advice is None and "short" in errors[0]


def test_copper_word_is_not_a_false_mention(record, profile):
    ok = dict(GOOD, summary="Broken copper trace (open) in zone A1.")
    assert validate(json.dumps(ok), record, profile)[0] is not None


def test_validate_missing_keys(record, profile):
    advice, errors = validate('{"summary": "x"}', record, profile)
    assert advice is None and any("likely_causes" in e for e in errors)


def test_validate_coerces_string_list(record, profile):
    advice, _ = validate(json.dumps(dict(GOOD, likely_causes="over-etching")), record, profile)
    assert advice["likely_causes"] == ["over-etching"]


def test_template_is_valid(record, profile):
    out = TemplateLLM(profile).advise(record)
    advice, errors = validate(out.text, record, profile)
    assert errors == [], errors
    assert "open" in advice["summary"]


def test_prompt_is_grounded(record, profile):
    msgs = build_messages(record, profile)
    roles = [r for r, _ in msgs]
    assert roles == ["system", "user", "assistant", "user"]
    final_user = msgs[-1][1]
    assert "over-etching" in final_user and "mousebite" not in final_user
    chat = llama3_chat(msgs)
    assert chat.endswith("<|start_header_id|>assistant<|end_header_id|>\n\n")
    assert chat.startswith("<|begin_of_text|>") and chat.count("<|begin_of_text|>") == 1


def test_parse_observer():
    line = ('PyTorchObserver {"prompt_tokens":600,"generated_tokens":101,"model_load_start_ms":1000,'
            '"model_load_end_ms":2500,"inference_start_ms":3000,"prompt_eval_end_ms":3800,'
            '"first_token_ms":3800,"inference_end_ms":8800,"aggregate_sampling_time_ms":20,'
            '"SCALING_FACTOR_UNITS_PER_SECOND":1000}')
    s = parse_observer("noise\n" + line + "\n")
    assert s["load_ms"] == 1500 and s["ttft_ms"] == 800 and s["total_ms"] == 5800
    assert abs(s["tok_s"] - 20.0) < 1e-9
    assert parse_observer("nothing") == {}


LOOPED = ('{"summary": "Unit failed with one high-severity open in zone A1.", "likely_causes": ["over-etching"], '
          '"recommended_actions": ["check etch time"], "verify": "Re-inspect the next 5 units.", "log_entry": "U-1 '
          + "FAIL open/high A1 " * 12 + 'FAIL op')


def test_repair_collapses_loop_and_closes(record, profile):
    assert validate(LOOPED, record, profile)[0] is None  # strict mode still rejects it
    notes = []
    advice, errs = validate(LOOPED, record, profile, notes)
    assert advice and not errs, errs
    assert advice["log_entry"].count("FAIL open/high A1") == 1
    assert "collapsed a repetition loop" in notes and "closed truncated JSON" in notes


def test_repair_drops_partial_key_and_still_requires_all_keys(record, profile):
    cut = '{"summary": "Unit failed.", "likely_causes": ["over-etching"], "recommended_actions": ["check etch"], "veri'
    notes = []
    advice, errs = validate(cut, record, profile, notes)
    assert advice is None and any("missing key" in e for e in errs)


def test_repair_cannot_smuggle_invented_defects(record, profile):
    cut = ('{"summary": "Open and short found.", "likely_causes": ["x"], "recommended_actions": ["y"], '
           '"verify": "z", "log_entry": "short circuit again')
    advice, errs = validate(cut, record, profile, [])
    assert advice is None and "not in record" in errs[0]


def test_missing_log_entry_is_filled_and_flagged(record, tmp_path):
    from qc.advisory import Advisor
    from qc.advisory.llm import LLMOutput
    from qc.config import load_config

    adv = Advisor(load_config(overrides=["advisory.backend=template"]))

    class NoLogLine:
        name = "executorch"

        def advise(self, rec):
            return LLMOutput(json.dumps({k: v for k, v in GOOD.items() if k != "log_entry"}), {})

    adv.primary = NoLogLine()
    res = adv.advise(record)
    assert res.valid and res.repaired and not res.fallback and res.backend == "executorch"
    assert res.advice["log_entry"].startswith("U-1 FAIL open")
    assert any("log_entry built from the record" in e for e in res.errors)


def as_review(record):
    import copy

    r = copy.deepcopy(record)
    r.inspection_result = "REVIEW"
    return r


def test_wrong_verdict_is_rejected_or_corrected(record, profile):
    from qc.advisory.validator import verdict_conflict

    r = as_review(record)
    advice, errors = validate(json.dumps(GOOD), r, profile)  # strict: "Unit failed" on a REVIEW unit
    assert advice is None and "verdict" in errors[0]
    notes = []
    advice, errors = validate(json.dumps(GOOD), r, profile, notes)
    assert errors == [] and any("verdict corrected" in n for n in notes)
    assert advice["summary"].startswith("REVIEW: ") and not verdict_conflict(advice["summary"], "REVIEW")
    assert not verdict_conflict(advice["log_entry"], "REVIEW")


def test_verdict_words_in_causes_are_not_conflicts():
    from qc.advisory.validator import verdict_conflict

    assert not verdict_conflict("REVIEW: oil stain, likely wiper failure.", "REVIEW")
    assert not verdict_conflict("U-1 FAIL open A1", "FAIL")
    assert not verdict_conflict("PASS WITH NOTE: one small pin-hole.", "PASS_WITH_NOTE")
    assert verdict_conflict("The unit passed inspection.", "REVIEW")


def test_defect_name_is_not_a_cause(record, profile):
    bad = {**GOOD, "likely_causes": [record.defect_classes[0]]}
    notes = []
    advice, errors = validate(json.dumps(bad), record, profile, notes)
    assert errors == [] and notes
    assert record.defect_classes[0] not in advice["likely_causes"]


def test_invented_counts_and_log_lines_in_verify_are_fixed(record, profile):
    bad = {**GOOD, "verify": f"{record.unit_id} FAIL: one open; 2nd open in last 50 units; check etch.",
           "log_entry": f"{record.unit_id} FAIL open; 9th open in last 50 units."}
    advice, errors = validate(json.dumps(bad), record, profile)
    assert advice is None and errors
    notes = []
    advice, errors = validate(json.dumps(bad), record, profile, notes)
    assert errors == [] and advice["verify"] == "Re-inspect the next 5 units for open."
    assert "last 50" not in advice["log_entry"] and notes


def test_counts_from_the_record_are_kept(record, profile):
    n, k = record.context["recent_units"], record.context["recent_defects"]["open"]
    ok = {**GOOD, "log_entry": f"{record.unit_id} FAIL open; {k}nd open in last {n} units."}
    advice, errors = validate(json.dumps(ok), record, profile)
    assert errors == [] and f"last {n} units" in advice["log_entry"]
