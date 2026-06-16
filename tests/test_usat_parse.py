from __future__ import annotations

import re
from pathlib import Path

from racedata.lifetime.models import LifetimeAthleteProfile, LifetimeRaceResult
from racedata.providers.usat.parse import (
    parse_finish_seconds,
    parse_profile_header,
    parse_results_page,
    parse_search_page,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_search_page_returns_candidates_with_disambiguation():
    profiles = parse_search_page(_read("usat_search_navratil.html"))
    assert len(profiles) >= 2
    joe = next(p for p in profiles if p.athlete_id == "182151")
    assert joe.last_name == "Navratil"
    assert joe.first_name == "Joe"
    assert joe.display_name == "Joe Navratil"
    assert joe.location == "Middleton, Wisconsin"
    assert joe.age == 49
    assert joe.gender == "Male"
    assert joe.provider == "usat"


def test_parse_profile_header():
    profile = parse_profile_header(_read("usat_athlete_182151_results_p1.html"), athlete_id="182151")
    assert profile is not None
    assert profile.display_name == "Joe Navratil"
    assert profile.age == 50
    assert profile.gender == "Male"
    assert profile.location == "Wisconsin"


def test_parse_results_page_first_page():
    results = parse_results_page(_read("usat_athlete_182151_results_p1.html"), athlete_id="182151")
    assert len(results) == 25
    first = results[0]
    assert first.event_id == "38240"
    assert first.race_id == "4261993"
    assert first.result_id == "6430734"
    assert first.position == 43
    assert first.ranking == 113.633
    assert first.finish_time == "1:10:02.000"
    assert first.finish_seconds == 4202.0
    assert "Multisport National Championships Festival" in first.event_name
    assert first.race_date == "Sat, May 16"


def test_parse_results_page_second_page_differs():
    page_one = parse_results_page(_read("usat_athlete_182151_results_p1.html"), athlete_id="182151")
    page_two = parse_results_page(_read("usat_athlete_182151_results_p2.html"), athlete_id="182151")
    assert page_one[0].result_id != page_two[0].result_id


def test_parse_finish_seconds_handles_fractional_hours():
    assert parse_finish_seconds("1:10:02.000") == 4202.0
    assert parse_finish_seconds("0:20:32.000") == 1232.0
