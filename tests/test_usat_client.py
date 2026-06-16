from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from racedata.providers.usat.client import UsatClient, UsatRateLimitError
from racedata.providers.usat.service import UsatLifetimeProvider

FIXTURES = Path(__file__).parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def _mock_response(*, status_code: int = 200, headers: dict | None = None, text: str = "") -> Mock:
    response = Mock()
    response.status_code = status_code
    response.headers = headers or {}
    response.text = text
    response.raise_for_status = Mock()
    if status_code >= 400:
        response.raise_for_status.side_effect = Exception(f"HTTP {status_code}")
    return response


def test_fetch_search_html():
    calls: list[str] = []

    def fetch(url: str) -> str:
        calls.append(url)
        return _read("usat_search_navratil.html")

    client = UsatClient(fetch_html=fetch)
    html = client.fetch_search_html("Navratil")
    assert "Navratil" in html
    assert calls == [
        "https://member.usatriathlon.org/results/athletes?search=Navratil"
    ]


def test_fetch_all_results_paginates_until_empty():
    pages = {
        1: _read("usat_athlete_182151_results_p1.html"),
        2: _read("usat_athlete_182151_results_p2.html"),
        3: "<html></html>",
    }

    def fetch(url: str) -> str:
        if "page=2" in url:
            return pages[2]
        if "page=3" in url:
            return pages[3]
        return pages[1]

    client = UsatClient(fetch_html=fetch)
    results = client.fetch_all_results("182151")
    assert len(results) == 50
    assert results[0].athlete_id == "182151"
    assert results[0].event_id == "38240"


def test_usat_lifetime_provider_search():
    provider = UsatLifetimeProvider(
        client=UsatClient(fetch_html=lambda _url: _read("usat_search_navratil.html"))
    )
    profiles = provider.search_athletes("Navratil")
    assert any(p.athlete_id == "182151" for p in profiles)


def test_usat_lifetime_provider_fetch_profile():
    provider = UsatLifetimeProvider(
        client=UsatClient(
            fetch_html=lambda _url: _read("usat_athlete_182151_results_p1.html")
        )
    )
    profile = provider.fetch_profile("182151")
    assert profile is not None
    assert profile.display_name == "Joe Navratil"


def test_usat_lifetime_provider_fetch_all_results():
    pages = {
        1: _read("usat_athlete_182151_results_p1.html"),
        2: _read("usat_athlete_182151_results_p2.html"),
        3: "<html></html>",
    }

    def fetch(url: str) -> str:
        if "page=2" in url:
            return pages[2]
        if "page=3" in url:
            return pages[3]
        return pages[1]

    provider = UsatLifetimeProvider(client=UsatClient(fetch_html=fetch))
    results = provider.fetch_all_results("182151")
    assert len(results) == 50


def test_fetch_profile_and_results_dedupes_page_one():
    pages = {
        1: _read("usat_athlete_182151_results_p1.html"),
        2: _read("usat_athlete_182151_results_p2.html"),
        3: "<html></html>",
    }
    calls: list[str] = []

    def fetch(url: str) -> str:
        calls.append(url)
        if "page=2" in url:
            return pages[2]
        if "page=3" in url:
            return pages[3]
        return pages[1]

    provider = UsatLifetimeProvider(client=UsatClient(fetch_html=fetch))
    profile, results = provider.fetch_profile_and_results("182151")
    assert profile is not None
    assert profile.display_name == "Joe Navratil"
    assert len(results) == 50
    assert calls == [
        "https://member.usatriathlon.org/athletes/182151/results",
        "https://member.usatriathlon.org/athletes/182151/results?page=2",
        "https://member.usatriathlon.org/athletes/182151/results?page=3",
    ]


def test_cache_hit_skips_second_network_request():
    client = UsatClient(cache_ttl_seconds=3600)
    response = _mock_response(
        status_code=200,
        headers={"x-ratelimit-remaining": "29"},
        text="<html>cached</html>",
    )
    with patch.object(client._session, "get", return_value=response) as mock_get:
        first = client._default_fetch("https://member.usatriathlon.org/test-cache")
        second = client._default_fetch("https://member.usatriathlon.org/test-cache")
    assert first == "<html>cached</html>"
    assert second == "<html>cached</html>"
    assert mock_get.call_count == 1


def test_cache_expires_after_ttl():
    now = [0.0]

    def monotonic() -> float:
        return now[0]

    client = UsatClient(cache_ttl_seconds=60.0, monotonic=monotonic, sleep=lambda _s: None)
    response = _mock_response(
        status_code=200,
        headers={"x-ratelimit-remaining": "29"},
        text="<html>fresh</html>",
    )
    with patch.object(client._session, "get", return_value=response) as mock_get:
        client._default_fetch("https://member.usatriathlon.org/test-expire")
        now[0] = 61.0
        client._default_fetch("https://member.usatriathlon.org/test-expire")
    assert mock_get.call_count == 2


def test_waits_when_rate_limit_remaining_is_low():
    sleeps: list[float] = []
    now = [0.0]

    def monotonic() -> float:
        return now[0]

    def sleep(seconds: float) -> None:
        sleeps.append(seconds)
        now[0] += seconds

    client = UsatClient(
        cache_ttl_seconds=0,
        monotonic=monotonic,
        sleep=sleep,
        rate_limit_window_seconds=60.0,
    )
    responses = [
        _mock_response(status_code=200, headers={"x-ratelimit-remaining": "1"}, text="page1"),
        _mock_response(status_code=200, headers={"x-ratelimit-remaining": "29"}, text="page2"),
    ]
    with patch.object(client._session, "get", side_effect=responses):
        client._default_fetch("https://member.usatriathlon.org/page1")
        client._default_fetch("https://member.usatriathlon.org/page2")
    assert sleeps
    assert sleeps[0] == pytest.approx(60.0)


def test_retries_after_429_then_succeeds():
    sleeps: list[float] = []
    client = UsatClient(
        cache_ttl_seconds=0,
        max_retries=3,
        sleep=lambda seconds: sleeps.append(seconds),
        monotonic=lambda: 0.0,
    )
    responses = [
        _mock_response(status_code=429, headers={"Retry-After": "5"}, text="slow down"),
        _mock_response(status_code=200, headers={"x-ratelimit-remaining": "29"}, text="ok"),
    ]
    with patch.object(client._session, "get", side_effect=responses):
        html = client._default_fetch("https://member.usatriathlon.org/retry")
    assert html == "ok"
    assert sleeps == [5.0]


def test_raises_rate_limit_error_after_exhausted_retries():
    client = UsatClient(
        cache_ttl_seconds=0,
        max_retries=2,
        sleep=lambda _seconds: None,
        monotonic=lambda: 0.0,
    )
    responses = [
        _mock_response(status_code=429, headers={"Retry-After": "1"}, text="slow down"),
        _mock_response(status_code=429, headers={"Retry-After": "1"}, text="slow down"),
    ]
    with patch.object(client._session, "get", side_effect=responses):
        with pytest.raises(UsatRateLimitError, match="try again in a minute"):
            client._default_fetch("https://member.usatriathlon.org/blocked")
