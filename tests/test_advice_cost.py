import json
from types import SimpleNamespace as NS

from qc.advisory.prompt import build_messages
from qc.advisory.worker import AdvisoryWorker
from qc.schema import Detection


def rec(name, result):
    return NS(unit_id=name, inspection_result=result)


def pending(w):
    return [it[0].unit_id for it in w.q.queue]


def test_priority_queue_keeps_failures():
    w = AdvisoryWorker(None, maxsize=2, prioritise=True)
    w.submit(rec("f1", "FAIL"))
    w.submit(rec("n1", "PASS_WITH_NOTE"))
    w.submit(rec("f2", "FAIL"))
    assert pending(w) == ["f1", "f2"]
    w.submit(rec("r1", "REVIEW"))
    assert pending(w) == ["f1", "f2"]
    w.submit(rec("f3", "FAIL"))
    assert pending(w) == ["f2", "f3"]
    assert w.dropped == 3 and w.q.unfinished_tasks == 2


def test_default_drops_oldest():
    w = AdvisoryWorker(None, maxsize=1)
    w.submit(rec("f", "FAIL"))
    w.submit(rec("n", "PASS_WITH_NOTE"))
    assert pending(w) == ["n"] and w.q.unfinished_tasks == 1


def test_compact_prompt_is_shorter_and_keeps_every_defect(record, profile):
    for i in range(6):
        record.detections.append(Detection("spur", 0.9, [i * 90, 10, i * 90 + 30, 40], severity="medium", zone="A1"))
    full, compact = (build_messages(record, profile, c) for c in (False, True))
    assert len(compact[-1][1]) < 0.75 * len(full[-1][1])
    view = json.loads(compact[-1][1].split("INSPECTION RECORD:\n")[1])
    assert {g["defect"]: g["count"] for g in view["detections"]} == {"open": 1, "spur": 6}
    assert view["detections"][0]["severity"] == "high"
