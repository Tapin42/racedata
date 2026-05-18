from racedata.core.comparison import (
    build_comparison_cell,
    build_comparison_rows,
    compute_delta,
    format_delta,
)
from racedata.core.models import AthleteRef, SegmentSplit


def _split(segment_id: str, label: str, clock: int, leg: int) -> SegmentSplit:
    return SegmentSplit(
        segment_id=segment_id,
        label=label,
        clock_time=f"{clock // 60}:{clock % 60:02d}",
        clock_seconds=clock,
        leg_time=f"{leg // 60}:{leg % 60:02d}",
        leg_seconds=leg,
    )


def test_compute_delta_positive_when_behind():
    assert compute_delta(1500, 1200) == 300


def test_format_delta_plus_five_minutes():
    assert format_delta(300) == "+5:00"


def test_build_comparison_cell_baseline_has_no_deltas():
    split = _split("SWIM", "Swim", 1200, 1200)
    cell = build_comparison_cell(split, split, is_baseline=True)
    assert cell.clock_delta_seconds is None
    assert cell.leg_delta_seconds is None


def test_build_comparison_cell_shows_dual_deltas():
    baseline = _split("SWIM", "Swim", 1200, 1200)
    athlete = _split("SWIM", "Swim", 1500, 1500)
    cell = build_comparison_cell(baseline, athlete, is_baseline=False)
    assert cell.clock_delta_seconds == 300
    assert cell.leg_delta_seconds == 300
    assert format_delta(cell.clock_delta_seconds) == "+5:00"


def test_build_comparison_rows_marks_baseline():
    athletes = [
        AthleteRef(profile_id="A", entry_id="1", name="Seed"),
        AthleteRef(profile_id="B", entry_id="2", name="Other"),
    ]
    splits = {
        "A": [_split("SWIM", "Swim", 1200, 1200)],
        "B": [_split("SWIM", "Swim", 1500, 1500)],
    }
    columns, rows = build_comparison_rows(athletes, splits, baseline_index=0)
    assert len(columns) == 1
    assert rows[0].is_baseline is True
    assert rows[1].cells[0].clock_delta_seconds == 300


def test_missing_segment_returns_dash():
    baseline = _split("SWIM", "Swim", 1200, 1200)
    cell = build_comparison_cell(baseline, None, is_baseline=False)
    assert cell.clock_time is None
    assert format_delta(cell.clock_delta_seconds) == "—"
