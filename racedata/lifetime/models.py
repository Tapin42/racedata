from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LifetimeAthleteProfile:
    provider: str
    athlete_id: str
    display_name: str
    first_name: str
    last_name: str
    age: int | None
    gender: str
    location: str


@dataclass(frozen=True)
class LifetimeRaceResult:
    provider: str
    athlete_id: str
    event_id: str
    race_id: str
    result_id: str
    event_name: str
    race_name: str
    race_date: str
    position: int | None
    ranking: float | None
    finish_time: str
    finish_seconds: float | None


@dataclass(frozen=True)
class HeadToHeadMatch:
    event_id: str
    race_id: str
    event_name: str
    race_name: str
    race_date: str
    result_a: LifetimeRaceResult
    result_b: LifetimeRaceResult

    @property
    def time_delta_seconds(self) -> float | None:
        if self.result_a.finish_seconds is None or self.result_b.finish_seconds is None:
            return None
        return self.result_b.finish_seconds - self.result_a.finish_seconds
