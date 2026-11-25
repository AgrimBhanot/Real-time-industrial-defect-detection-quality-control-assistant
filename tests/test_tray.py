import cv2
import numpy as np
import pytest

from qc.config import load_config
from qc.rules import RuleEngine
from qc.sources import Frame, PartsTrigger
from qc.vision.tray import RustCheck, TrayDetector


def part(kind, x, y):
    return {"type": kind, "bbox": [x - 50, y - 50, x + 50, y + 50]}


def test_parts_trigger_fires_once_per_arrangement():
    t = PartsTrigger(frames=3)
    tray = [part("nut", 100, 100), part("bolt", 400, 300)]
    assert [t.update(tray) for _ in range(8)] == [False, False, False, True, False, False, False, False]
    moved = [part("nut", 200, 100), part("bolt", 400, 300)]
    assert sum(t.update(moved) for _ in range(8)) == 1          # one part moved
    assert sum(t.update(moved[:1]) for _ in range(8)) == 1      # one part removed
    assert sum(t.update([]) for _ in range(8)) == 0             # an empty tray is not a unit
    assert sum(t.update(moved[:1]) for _ in range(8)) == 1      # the same part put back is


def test_parts_trigger_ignores_jitter_and_motion():
    t = PartsTrigger(frames=3)
    assert sum(t.update([part("nut", 100 + i % 3, 100)]) for i in range(20)) == 1
    assert not any(t.update([part("nut", 100 + 30 * i, 100)]) for i in range(20))


def scene():
    img = np.full((400, 800, 3), 30, np.uint8)
    out = []
    for x, colour in ((200, (120, 125, 122)), (600, (45, 80, 115))):  # grey part, rust-brown part (BGR)
        cv2.circle(img, (x, 200), 90, colour, -1)
        th = np.linspace(0, 2 * np.pi, 60)
        out.append(([x - 90, 110, x + 90, 290], 0.9, "washer", np.c_[x + 90 * np.cos(th), 200 + 90 * np.sin(th)]))
    return img, out


def detector(roi=(0, 0, 1, 1)):
    det = TrayDetector.__new__(TrayDetector)
    det.roi, det.rust = roi, RustCheck()
    return det


def test_only_the_rusty_part_is_flagged():
    img, found = scene()
    f = Frame(img, "t", "camera")
    dets = detector().check(f, found)
    assert [p["id"] for p in f.parts] == ["washer 1", "washer 2"]
    assert len(dets) == 1 and dets[0].part == "washer 2" and dets[0].size > 0.8
    rules = RuleEngine(load_config(overrides=["profile=tray"]).profile)
    trace = rules.annotate(dets, 800, 400)
    assert dets[0].size_unit == "part_frac" and dets[0].size > 0.8  # not overwritten by the frame fraction
    assert rules.decide(dets)[0] == "FAIL" and trace[0].startswith("washer 2: rust")


def test_bright_yellow_is_not_rust_and_roi_excludes():
    img, found = scene()
    cv2.circle(img, (600, 200), 90, (110, 190, 215), -1)  # zinc-yellow plating
    f = Frame(img, "t", "camera")
    assert detector().check(f, found) == []
    detector(roi=(0, 0, 0.5, 1)).check(f, found)
    assert len(f.parts) == 1


def test_profile_app_settings_and_cli_order():
    assert load_config(overrides=["profile=metal_parts"]).section("vision")["imgsz"] == 960
    assert load_config(overrides=["profile=metal_parts", "vision.imgsz=640"]).section("vision")["imgsz"] == 640
    assert load_config(overrides=["profile=pcb"]).section("vision")["imgsz"] == 640


@pytest.mark.parametrize("name", ["tray", "metal_parts", "steel_sheet", "pcb", "mvtec_fasteners"])
def test_profiles_are_consistent(name):
    p = load_config(overrides=[f"profile={name}"]).profile
    assert set(p["severity"]["classes"]) == set(p["classes"]) and set(p["classes"]) <= set(p["sop"])
    # no defect's phrase may also match another defect's SOP text: the faithfulness check would reject good advice
    from qc.advisory.validator import mentioned_classes
    for c in p["classes"]:
        text = "; ".join(p["sop"][c]["causes"] + p["sop"][c]["actions"])
        assert mentioned_classes(text, p) <= {c}, (c, text)
