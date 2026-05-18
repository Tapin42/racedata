from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Race:
    event_key: str
    display_name: str
    provider: str = "rtrt"
    app_id: str = ""


@dataclass(frozen=True)
class Course:
    id: str
    label: str


@dataclass(frozen=True)
class AthleteRef:
    profile_id: str
    entry_id: str
    name: str
    bib: str = ""
    division: str = ""


@dataclass(frozen=True)
class SegmentSplit:
    segment_id: str
    label: str
    clock_time: str
    clock_seconds: int
    leg_time: str | None = None
    leg_seconds: int | None = None
    is_intermediate: bool = False
    course: str | None = None


@dataclass(frozen=True)
class SegmentColumn:
    segment_id: str
    label: str


@dataclass(frozen=True)
class ComparisonCell:
    clock_time: str | None
    leg_time: str | None
    clock_seconds: int | None = None
    leg_seconds: int | None = None
    clock_delta_seconds: int | None = None
    leg_delta_seconds: int | None = None


@dataclass
class ComparisonRow:
    athlete: AthleteRef
    is_baseline: bool = False
    cells: list[ComparisonCell] = field(default_factory=list)
