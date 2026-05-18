import json
from pathlib import Path

import pytest

from racedata.core.timing import (
    derive_leg_seconds,
    format_hhmmss,
    normalize_segment_rows,
    parse_hhmmss,
    parse_leg_from_row,
    strip_fractional_time,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_hhmmss_handles_hms():
    assert parse_hhmmss("1:37:00") == 5820


def test_parse_hhmmss_handles_ms():
    assert parse_hhmmss("25:00") == 1500


def test_strip_fractional_time():
    assert strip_fractional_time("00:36:08.951") == "00:36:08"


def test_parse_leg_from_row_prefers_leg_time():
    leg_time, leg_seconds = parse_leg_from_row({"legTime": "00:36:08.951"})
    assert leg_time == "00:36:08"
    assert leg_seconds == 2168


def test_derive_leg_seconds_from_clock():
    assert derive_leg_seconds(5820, 1500) == 4320


def test_normalize_segment_rows_derives_missing_leg():
    rows = [
        {"point": "START", "label": "Start", "time": "00:00:00.00"},
        {"point": "SWIM", "label": "Swim", "time": "00:20:00.00"},
    ]
    splits = normalize_segment_rows(rows)
    assert splits[1].clock_seconds == 1200
    assert splits[1].leg_seconds == 1200


def test_format_hhmmss_signed_delta():
    assert format_hhmmss(300, signed=True) == "+5:00"
    assert format_hhmmss(-90, signed=True) == "-1:30"


def test_normalize_from_usat_fixture():
    payload = json.loads((FIXTURES / "usat_olympic_splits.json").read_text())
    rows = payload.get("list") or payload.get("splits") or []
    splits = normalize_segment_rows(rows, course_id="tri_olympic")
    labels = [split.label for split in splits]
    assert "Swim" in labels
    assert "T1" in labels
    assert any("Bike 3.4mi" in label for label in labels)
