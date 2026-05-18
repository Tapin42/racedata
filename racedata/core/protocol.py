from __future__ import annotations

from typing import Protocol

from racedata.core.models import AthleteRef, Course, Race, SegmentSplit


class TimingProvider(Protocol):
    def search_athletes(self, race: Race, query: str) -> list[AthleteRef]: ...

    def fetch_profile(self, race: Race, profile_id: str) -> AthleteRef | None: ...

    def fetch_splits(
        self,
        race: Race,
        profile_id: str,
        *,
        entry_id: str | None = None,
        course_id: str | None = None,
    ) -> list[SegmentSplit]: ...

    def list_courses(self, race: Race) -> list[Course]: ...
