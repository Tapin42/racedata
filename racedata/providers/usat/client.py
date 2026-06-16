from __future__ import annotations

import os
import time
from typing import Callable
from urllib.parse import quote

import requests

from racedata.lifetime.models import LifetimeRaceResult
from racedata.providers.usat.parse import parse_results_page

BASE_URL = "https://member.usatriathlon.org"
DEFAULT_USER_AGENT = "head2head-lifetime/1.0"
DEFAULT_RATE_LIMIT_WINDOW_SECONDS = 60.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_CACHE_TTL_SECONDS = 3600.0
LOW_REMAINING_THRESHOLD = 2
MIN_REQUEST_INTERVAL_SECONDS = 1.0


class UsatRateLimitError(Exception):
    """Raised when USAT blocks requests after exhausting retries."""


def _parse_int_header(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


class UsatClient:
    def __init__(
        self,
        *,
        fetch_html: Callable[[str], str] | None = None,
        base_url: str = BASE_URL,
        user_agent: str = DEFAULT_USER_AGENT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        cache_ttl_seconds: float | None = None,
        rate_limit_window_seconds: float = DEFAULT_RATE_LIMIT_WINDOW_SECONDS,
        sleep: Callable[[float], None] | None = None,
        monotonic: Callable[[], float] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._fetch_html = fetch_html or self._default_fetch
        self._max_retries = max_retries
        self._rate_limit_window_seconds = rate_limit_window_seconds
        self._sleep = sleep or time.sleep
        self._monotonic = monotonic or time.monotonic
        self._cache_ttl = (
            cache_ttl_seconds
            if cache_ttl_seconds is not None
            else float(os.getenv("USAT_CACHE_TTL_SECONDS", str(DEFAULT_CACHE_TTL_SECONDS)))
        )
        self._cache: dict[str, tuple[float, str]] = {}
        self._rate_limit_remaining: int | None = None
        self._rate_limit_reset_at: float | None = None
        self._last_request_at: float | None = None
        self._session = requests.Session()
        self._session.headers["User-Agent"] = user_agent

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

    def _get_cached(self, url: str) -> str | None:
        if self._cache_ttl <= 0:
            return None
        entry = self._cache.get(url)
        if entry is None:
            return None
        stored_at, html = entry
        if self._monotonic() - stored_at > self._cache_ttl:
            del self._cache[url]
            return None
        return html

    def _set_cached(self, url: str, html: str) -> None:
        if self._cache_ttl <= 0:
            return
        self._cache[url] = (self._monotonic(), html)

    def _wait_for_rate_limit(self) -> None:
        now = self._monotonic()
        if self._rate_limit_remaining is not None and self._rate_limit_remaining <= 1:
            wait_until = self._rate_limit_reset_at or (now + self._rate_limit_window_seconds)
            delay = max(0.0, wait_until - now)
            if delay > 0:
                self._sleep(delay)
            self._rate_limit_remaining = None
            self._rate_limit_reset_at = None
            return

        if (
            self._rate_limit_remaining is not None
            and self._rate_limit_remaining <= LOW_REMAINING_THRESHOLD
            and self._last_request_at is not None
        ):
            elapsed = now - self._last_request_at
            if elapsed < MIN_REQUEST_INTERVAL_SECONDS:
                self._sleep(MIN_REQUEST_INTERVAL_SECONDS - elapsed)

    def _update_rate_limit_from_response(self, response: requests.Response) -> None:
        remaining = _parse_int_header(response.headers.get("x-ratelimit-remaining"))
        if remaining is None:
            return
        self._rate_limit_remaining = remaining
        if remaining <= 1:
            retry_after = _parse_int_header(response.headers.get("Retry-After"))
            wait = retry_after if retry_after is not None else int(self._rate_limit_window_seconds)
            self._rate_limit_reset_at = self._monotonic() + wait

    def _default_fetch(self, url: str) -> str:
        cached = self._get_cached(url)
        if cached is not None:
            return cached

        for attempt in range(self._max_retries):
            self._wait_for_rate_limit()
            self._last_request_at = self._monotonic()
            response = self._session.get(url, timeout=20)

            if response.status_code == 429:
                retry_after = _parse_int_header(response.headers.get("Retry-After"))
                wait = retry_after if retry_after is not None else int(self._rate_limit_window_seconds)
                self._rate_limit_remaining = 0
                self._rate_limit_reset_at = self._monotonic() + wait
                if attempt < self._max_retries - 1:
                    self._sleep(wait)
                    self._rate_limit_remaining = None
                    self._rate_limit_reset_at = None
                    continue
                raise UsatRateLimitError(
                    "USAT is temporarily limiting requests; try again in a minute."
                )

            response.raise_for_status()
            self._update_rate_limit_from_response(response)
            html = response.text
            self._set_cached(url, html)
            return html

        raise UsatRateLimitError("USAT is temporarily limiting requests; try again in a minute.")
