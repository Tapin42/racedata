from pathlib import Path

import pytest

from racedata.providers.usat.client import UsatClient
from racedata.providers.usat.service import UsatLifetimeProvider

FIXTURES = Path(__file__).parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


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
