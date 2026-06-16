from __future__ import annotations

from racedata.lifetime.models import LifetimeAthleteProfile, LifetimeRaceResult
from racedata.providers.usat.client import UsatClient
from racedata.providers.usat.parse import parse_profile_header, parse_search_page


class UsatLifetimeProvider:
    def __init__(self, *, client: UsatClient | None = None) -> None:
        self._client = client or UsatClient()

    def search_athletes(self, query: str) -> list[LifetimeAthleteProfile]:
        html = self._client.fetch_search_html(query)
        return parse_search_page(html)

    def fetch_profile(self, athlete_id: str) -> LifetimeAthleteProfile | None:
        html = self._client.fetch_athlete_results_html(athlete_id)
        return parse_profile_header(html, athlete_id=athlete_id)

    def fetch_all_results(self, athlete_id: str) -> list[LifetimeRaceResult]:
        return self._client.fetch_all_results(athlete_id)
