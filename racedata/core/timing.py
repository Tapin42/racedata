from __future__ import annotations

import re

from racedata.core.models import SegmentSplit

DISTANCE_PATTERN = re.compile(r"\d+(?:[.,]\d+)?\s*(?:mi|km|m\b)", re.IGNORECASE)
LABEL_BLOCKLIST = {"announcer"}


def parse_hhmmss(value: str | None) -> int | None:
    if not value:
        return None
    text = str(value).strip().split(".")[0]
    parts = text.split(":")
    try:
        if len(parts) == 3:
            hours, minutes, seconds = (int(p) for p in parts)
        elif len(parts) == 2:
            hours = 0
            minutes, seconds = (int(p) for p in parts)
        else:
            return None
    except ValueError:
        return None
    return hours * 3600 + minutes * 60 + seconds


def format_hhmmss(total_seconds: int | None, *, signed: bool = False) -> str:
    if total_seconds is None:
        return "—"
    sign = ""
    value = total_seconds
    if signed:
        if value > 0:
            sign = "+"
        elif value < 0:
            sign = "-"
        value = abs(value)
    hours = value // 3600
    minutes = (value % 3600) // 60
    seconds = value % 60
    if hours:
        return f"{sign}{hours}:{minutes:02d}:{seconds:02d}"
    return f"{sign}{minutes}:{seconds:02d}"


def strip_fractional_time(value: str | None) -> str:
    if not value:
        return ""
    return str(value).strip().split(".")[0]


def has_distance_marker(label: str) -> bool:
    return bool(DISTANCE_PATTERN.search(label or ""))


def is_blocked_label(label: str) -> bool:
    return (label or "").strip().lower() in LABEL_BLOCKLIST


def parse_clock_from_row(row: dict) -> tuple[str, int | None]:
    clock_raw = strip_fractional_time(row.get("time") or row.get("netTime"))
    return clock_raw, parse_hhmmss(clock_raw)


def parse_leg_from_row(row: dict) -> tuple[str | None, int | None]:
    for key in ("legTime", "splitTime", "netTime"):
        raw = row.get(key)
        if not raw:
            continue
        leg_raw = strip_fractional_time(str(raw))
        seconds = parse_hhmmss(leg_raw)
        if seconds is not None:
            return leg_raw, seconds
    return None, None


def parse_run_distance(split_name: str) -> float | None:
    text = (split_name or "").upper()
    normalized_text = re.sub(r"(?<=\d),(?=\d)", ".", text)

    mile_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:MI|MILE)\b", normalized_text)
    if mile_match:
        return float(mile_match.group(1))

    km_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:KM|K)\b", normalized_text)
    if km_match:
        return float(km_match.group(1)) * 0.621371

    meter_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:M|METER|METERS)\b", normalized_text)
    if meter_match:
        return float(meter_match.group(1)) / 1609.344

    return None


def derive_leg_seconds(clock_seconds: int | None, previous_clock: int | None) -> int | None:
    if clock_seconds is None or previous_clock is None:
        return None
    delta = clock_seconds - previous_clock
    return delta if delta >= 0 else None


def normalize_segment_rows(
    rows: list[dict],
    *,
    course_id: str | None = None,
) -> list[SegmentSplit]:
    normalized: list[SegmentSplit] = []
    previous_clock: int | None = None

    for row in rows:
        if not isinstance(row, dict):
            continue
        if course_id and row.get("course") and row.get("course") != course_id:
            continue

        label = str(
            row.get("label") or row.get("split") or row.get("point") or row.get("name") or ""
        ).strip()
        segment_id = str(row.get("point") or row.get("name") or label).strip()
        if not label or not segment_id:
            continue

        clock_time, clock_seconds = parse_clock_from_row(row)
        if clock_seconds is None:
            continue

        leg_time, leg_seconds = parse_leg_from_row(row)
        if leg_seconds is None:
            leg_seconds = derive_leg_seconds(clock_seconds, previous_clock)
            leg_time = format_hhmmss(leg_seconds) if leg_seconds is not None else None

        normalized.append(
            SegmentSplit(
                segment_id=segment_id,
                label=label,
                clock_time=clock_time,
                clock_seconds=clock_seconds,
                leg_time=leg_time,
                leg_seconds=leg_seconds,
                is_intermediate=has_distance_marker(label),
                course=row.get("course"),
            )
        )
        previous_clock = clock_seconds

    return normalized
