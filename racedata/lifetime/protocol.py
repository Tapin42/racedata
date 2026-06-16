from __future__ import annotations

from typing import Protocol

from racedata.lifetime.models import LifetimeAthleteProfile, LifetimeRaceResult


class LifetimeResultsProvider(Protocol):
    def search_athletes(self, query: str) -> list[LifetimeAthleteProfile]: ...

    def fetch_profile(self, athlete_id: str) -> LifetimeAthleteProfile | None: ...

    def fetch_all_results(self, athlete_id: str) -> list[LifetimeRaceResult]: ...
