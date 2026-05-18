from __future__ import annotations

from racedata.core.models import SegmentSplit
from racedata.core.timing import has_distance_marker, is_blocked_label


def main_point_names_from_conf(pointorder: list[dict], course_id: str | None = None) -> set[str]:
    names: set[str] = set()
    for point in pointorder:
        if not isinstance(point, dict):
            continue
        if course_id and point.get("course") != course_id:
            continue
        label = str(point.get("label") or point.get("name") or "").strip()
        name = str(point.get("name") or "").strip()
        if not label or is_blocked_label(label):
            continue
        if has_distance_marker(label):
            continue
        if name:
            names.add(name)
    return names


def is_main_segment(
    split: SegmentSplit,
    *,
    allowed_point_names: set[str] | None = None,
) -> bool:
    if is_blocked_label(split.label):
        return False
    if allowed_point_names:
        return split.segment_id in allowed_point_names
    return not has_distance_marker(split.label) and not split.is_intermediate


def collapse_intermediate_splits(
    splits: list[SegmentSplit],
    *,
    allowed_point_names: set[str] | None = None,
) -> list[SegmentSplit]:
    return [
        split
        for split in splits
        if is_main_segment(split, allowed_point_names=allowed_point_names)
    ]


def unique_courses(splits: list[SegmentSplit]) -> list[str]:
    seen: list[str] = []
    for split in splits:
        if split.course and split.course not in seen:
            seen.append(split.course)
    return seen


def filter_splits_by_course(splits: list[SegmentSplit], course_id: str | None) -> list[SegmentSplit]:
    if not course_id:
        return splits
    return [split for split in splits if split.course == course_id]
