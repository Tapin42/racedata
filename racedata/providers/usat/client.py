from __future__ import annotations

from typing import Callable
from urllib.parse import quote

import requests

from racedata.lifetime.models import LifetimeRaceResult
from racedata.providers.usat.parse import parse_results_page

BASE_URL = "https://member.usatriathlon.org"


class UsatClient:
    def __init__(
        self,
        *,
        fetch_html: Callable[[str], str] | None = None,
        base_url: str = BASE_URL,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._fetch_html = fetch_html or self._default_fetch

    def fetch_search_html(self, query: str) -> str:
        url = f"{self.base_url}/results/athletes?search={quote(query)}"
        return self._fetch_html(url)

    def fetch_athlete_results_html(self, athlete_id: str, *, page: int = 1) -> str:
        if page <= 1:
            url = f"{self.base_url}/athletes/{athlete_id}/results"
        else:
            url = f"{self.base_url}/athletes/{athlete_id}/results?page={page}"
        return self._fetch_html(url)

    def fetch_all_results(self, athlete_id: str) -> list[LifetimeRaceResult]:
        results: list[LifetimeRaceResult] = []
        page = 1
        while True:
            html = self.fetch_athlete_results_html(athlete_id, page=page)
            page_results = parse_results_page(html, athlete_id=athlete_id)
            if not page_results:
                break
            results.extend(page_results)
            page += 1
        return results

    def _default_fetch(self, url: str) -> str:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        return response.text
