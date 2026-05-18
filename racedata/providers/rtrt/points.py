from __future__ import annotations

from racedata.core.models import Course


def course_labels_from_conf(conf: dict) -> dict[str, str]:
    labels: dict[str, str] = {}
    allpoints = conf.get("tools", {}).get("allpoints", [])
    if not isinstance(allpoints, list):
        return labels
    for point in allpoints:
        if not isinstance(point, dict):
            continue
        course = str(point.get("course") or "").strip()
        race = str(point.get("race") or "").strip()
        if course and race and course not in labels:
            labels[course] = race
    return labels


def list_courses_from_conf(conf: dict) -> list[Course]:
    labels = course_labels_from_conf(conf)
    return [Course(id=course_id, label=label) for course_id, label in sorted(labels.items())]


def pointorder_for_course(conf: dict, course_id: str | None = None) -> list[dict]:
    pointorder = conf.get("vconf", {}).get("pointorder") or []
    if not isinstance(pointorder, list):
        return []
    if not course_id:
        return [point for point in pointorder if isinstance(point, dict)]
    return [
        point
        for point in pointorder
        if isinstance(point, dict) and point.get("course") == course_id
    ]


def default_course_from_splits(splits: list[dict]) -> str | None:
    counts: dict[str, int] = {}
    latest: dict[str, float] = {}
    for row in splits:
        if not isinstance(row, dict):
            continue
        course = row.get("course")
        if not course:
            continue
        counts[course] = counts.get(course, 0) + 1
        ts = float(row.get("timestamp") or row.get("epochTime") or 0)
        if ts >= latest.get(course, 0):
            latest[course] = ts
    if not counts:
        return None
    if len(counts) == 1:
        return next(iter(counts))
    return max(latest, key=lambda key: latest[key])
