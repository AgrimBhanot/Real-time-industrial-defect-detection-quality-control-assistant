import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

from qc.config import load_profile  # noqa: E402
from qc.rules import RuleEngine  # noqa: E402
from qc.schema import Detection, InspectionRecord  # noqa: E402


@pytest.fixture
def profile():
    return load_profile("pcb")


@pytest.fixture
def record(profile):
    dets = [Detection("open", 0.94, [120, 80, 160, 110])]
    rules = RuleEngine(profile)
    trace = rules.annotate(dets, 640, 640)
    result, why = rules.decide(dets)
    return InspectionRecord("U-1", "t", "test", "-", [640, 640], dets, result, trace + why,
                            {"station": "AOI-1", "recent_units": 10, "recent_fail": 2, "recent_defects": {"open": 2}})
