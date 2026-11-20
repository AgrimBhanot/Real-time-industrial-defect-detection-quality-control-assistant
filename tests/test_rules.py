import pytest

from qc.config import load_profile
from qc.rules import RuleEngine
from qc.schema import Detection


@pytest.fixture
def engine():
    p = load_profile("pcb")
    p["severity"]["size_thresholds"] = {"mousebite": [0.02, 0.06], "spur": [0.02, 0.06], "copper": [0.02, 0.06],
                                        "pin-hole": [0.01, 0.03]}
    return RuleEngine(p)


def box_mm2(mm2, ppm=48.0, x=100, y=100):
    side = (mm2 ** 0.5) * ppm
    return [x, y, round(x + side), round(y + side)]


def run(engine, dets):
    engine.annotate(dets, 640, 640)
    return engine.decide(dets)[0]


def test_no_defects_pass(engine):
    assert run(engine, []) == "PASS"


@pytest.mark.parametrize("cls", ["open", "short"])
def test_critical_classes_always_fail(engine, cls):
    d = Detection(cls, 0.9, box_mm2(0.001))
    assert run(engine, [d]) == "FAIL"
    assert d.severity == "high"


def test_size_escalation_three_level(engine):
    small, mid, big = (Detection("spur", 0.9, box_mm2(a)) for a in (0.01, 0.04, 0.1))
    engine.annotate([small, mid, big], 640, 640)
    assert (small.severity, mid.severity, big.severity) == ("low", "medium", "high")


def test_pinhole_escalates_only(engine):
    small, big = Detection("pin-hole", 0.9, box_mm2(0.001)), Detection("pin-hole", 0.9, box_mm2(0.05))
    engine.annotate([small, big], 640, 640)
    assert (small.severity, big.severity) == ("low", "medium")


def test_medium_counts(engine):
    one = [Detection("spur", 0.9, box_mm2(0.04))]
    two = one + [Detection("copper", 0.9, box_mm2(0.04, x=300))]
    assert run(engine, one) == "REVIEW"
    assert run(engine, two) == "FAIL"


def test_low_only_pass_with_note(engine):
    assert run(engine, [Detection("pin-hole", 0.9, box_mm2(0.001))]) == "PASS_WITH_NOTE"


def test_low_confidence_needs_review_not_downgrade(engine):
    d = Detection("open", 0.2, box_mm2(0.01))
    result = run(engine, [d])
    assert d.needs_review and d.severity == "high"
    assert result == "REVIEW"


def test_zone_grid(engine):
    assert engine.zone(Detection("spur", 1, [0, 0, 10, 10]), 640, 640) == "A1"
    assert engine.zone(Detection("spur", 1, [630, 630, 640, 640]), 640, 640) == "C3"
    assert engine.zone(Detection("spur", 1, [310, 310, 330, 330]), 640, 640) == "B2"


def test_fasteners_profile_uses_frame_fraction():
    e = RuleEngine(load_profile("fasteners"))
    d = Detection("rust", 0.9, [0, 0, 64, 64])
    e.annotate([d], 640, 640)
    assert d.size_unit == "frame_frac" and abs(d.size - 0.01) < 1e-9
