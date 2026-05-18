import json
from pathlib import Path

from racedata.core.split_filter import (
    collapse_intermediate_splits,
    main_point_names_from_conf,
)
from racedata.core.timing import normalize_segment_rows
from racedata.providers.rtrt.points import pointorder_for_course

FIXTURES = Path(__file__).parent / "fixtures"


def _load_splits(name: str, course_id: str | None = None):
    payload = json.loads((FIXTURES / name).read_text())
    rows = payload.get("list") or payload.get("splits") or []
    return normalize_segment_rows(rows, course_id=course_id)


def test_collapse_venice703_intermediates():
    conf = json.loads((FIXTURES / "venice703_conf.json").read_text())
    allowed = main_point_names_from_conf(conf["vconf"]["pointorder"])
    splits = _load_splits("venice703_splits.json")
    main = collapse_intermediate_splits(splits, allowed_point_names=allowed)
    labels = [split.label for split in main]
    assert labels == ["Start", "Swim", "T1", "T2", "Finish"]


def test_collapse_usat_olympic_keeps_swim_t1_t2():
    conf = json.loads((FIXTURES / "usat_olympic_conf.json").read_text())
    allowed = main_point_names_from_conf(
        pointorder_for_course(conf, "tri_olympic"),
        course_id="tri_olympic",
    )
    splits = _load_splits("usat_olympic_splits.json", course_id="tri_olympic")
    main = collapse_intermediate_splits(splits, allowed_point_names=allowed)
    labels = [split.label for split in main]
    assert "Swim" in labels
    assert "T1" in labels
    assert "T2" in labels
    assert "Finish" in labels
    assert not any("Bike 3.4mi" in label for label in labels)


def test_heuristic_fallback_excludes_distance_labels():
    splits = _load_splits("venice703_splits.json")
    main = collapse_intermediate_splits(splits)
    assert not any("km" in split.label.lower() for split in main)
