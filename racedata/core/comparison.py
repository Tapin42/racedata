from __future__ import annotations

from racedata.core.models import (
    AthleteRef,
    ComparisonCell,
    ComparisonRow,
    SegmentColumn,
    SegmentSplit,
)
from racedata.core.timing import format_hhmmss


def segment_columns(main_splits: list[SegmentSplit]) -> list[SegmentColumn]:
    return [
        SegmentColumn(segment_id=split.segment_id, label=split.label)
        for split in main_splits
    ]


def align_segments(
    baseline_splits: list[SegmentSplit],
    athlete_splits: list[SegmentSplit],
) -> list[tuple[SegmentSplit | None, SegmentSplit | None]]:
    baseline_by_id = {split.segment_id: split for split in baseline_splits}
    athlete_by_id = {split.segment_id: split for split in athlete_splits}
    ordered_ids = [split.segment_id for split in baseline_splits]
    for split in athlete_splits:
        if split.segment_id not in ordered_ids:
            ordered_ids.append(split.segment_id)

    aligned: list[tuple[SegmentSplit | None, SegmentSplit | None]] = []
    for segment_id in ordered_ids:
        aligned.append((baseline_by_id.get(segment_id), athlete_by_id.get(segment_id)))
    return aligned


def compute_delta(athlete_value: int | None, baseline_value: int | None) -> int | None:
    if athlete_value is None or baseline_value is None:
        return None
    return athlete_value - baseline_value


def build_comparison_cell(
    baseline_split: SegmentSplit | None,
    athlete_split: SegmentSplit | None,
    *,
    is_baseline: bool,
) -> ComparisonCell:
    if athlete_split is None:
        return ComparisonCell(clock_time=None, leg_time=None)

    clock_time = athlete_split.clock_time
    leg_time = athlete_split.leg_time
    clock_seconds = athlete_split.clock_seconds
    leg_seconds = athlete_split.leg_seconds

    if is_baseline:
        return ComparisonCell(
            clock_time=clock_time,
            leg_time=leg_time,
            clock_seconds=clock_seconds,
            leg_seconds=leg_seconds,
        )

    clock_delta = compute_delta(
        athlete_split.clock_seconds,
        baseline_split.clock_seconds if baseline_split else None,
    )
    leg_delta = compute_delta(
        athlete_split.leg_seconds,
        baseline_split.leg_seconds if baseline_split else None,
    )
    return ComparisonCell(
        clock_time=clock_time,
        leg_time=leg_time,
        clock_seconds=clock_seconds,
        leg_seconds=leg_seconds,
        clock_delta_seconds=clock_delta,
        leg_delta_seconds=leg_delta,
    )


def build_comparison_rows(
    athletes: list[AthleteRef],
    splits_by_profile: dict[str, list[SegmentSplit]],
    *,
    baseline_index: int = 0,
) -> tuple[list[SegmentColumn], list[ComparisonRow]]:
    if not athletes:
        return [], []

    baseline_pid = athletes[baseline_index].profile_id
    baseline_splits = splits_by_profile.get(baseline_pid, [])
    columns = segment_columns(baseline_splits)

    rows: list[ComparisonRow] = []
    for index, athlete in enumerate(athletes):
        is_baseline = index == baseline_index
        athlete_splits = splits_by_profile.get(athlete.profile_id, [])
        aligned = align_segments(baseline_splits, athlete_splits)
        cells = [
            build_comparison_cell(base, ath, is_baseline=is_baseline)
            for base, ath in aligned
        ]
        rows.append(
            ComparisonRow(athlete=athlete, is_baseline=is_baseline, cells=cells)
        )

    return columns, rows


def format_delta(seconds: int | None) -> str:
    if seconds is None:
        return "—"
    return format_hhmmss(seconds, signed=True)
