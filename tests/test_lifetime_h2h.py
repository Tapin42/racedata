from racedata.lifetime.h2h import find_common_races
from racedata.lifetime.models import LifetimeRaceResult


def _result(
    athlete_id: str,
    event_id: str,
    race_id: str,
    *,
    event_name: str = "Event",
    race_name: str = "Race",
    race_date: str = "2025-06-01",
    position: int | None = 10,
    ranking: float | None = 100.0,
    finish_time: str = "1:00:00.000",
    finish_seconds: float | None = 3600.0,
    result_id: str = "1",
) -> LifetimeRaceResult:
    return LifetimeRaceResult(
        provider="usat",
        athlete_id=athlete_id,
        event_id=event_id,
        race_id=race_id,
        result_id=result_id,
        event_name=event_name,
        race_name=race_name,
        race_date=race_date,
        position=position,
        ranking=ranking,
        finish_time=finish_time,
        finish_seconds=finish_seconds,
    )


def test_find_common_races_returns_intersection():
    a_results = [
        _result("1", "100", "200", race_date="2025-06-01", event_name="Shared Event"),
        _result("1", "101", "201", race_date="2024-01-01", event_name="A Only"),
    ]
    b_results = [
        _result("2", "100", "200", race_date="2025-06-01", event_name="Shared Event"),
        _result("2", "102", "202", race_date="2023-01-01", event_name="B Only"),
    ]
    matches = find_common_races(a_results, b_results)
    assert len(matches) == 1
    match = matches[0]
    assert match.event_id == "100"
    assert match.race_id == "200"
    assert match.event_name == "Shared Event"
    assert match.result_a.athlete_id == "1"
    assert match.result_b.athlete_id == "2"


def test_find_common_races_sorts_by_date_descending():
    a_results = [
        _result("1", "100", "200", race_date="2024-01-01"),
        _result("1", "101", "201", race_date="2025-06-01"),
    ]
    b_results = [
        _result("2", "100", "200", race_date="2024-01-01"),
        _result("2", "101", "201", race_date="2025-06-01"),
    ]
    matches = find_common_races(a_results, b_results)
    assert [m.race_date for m in matches] == ["2025-06-01", "2024-01-01"]


def test_find_common_races_empty_when_no_overlap():
    a_results = [_result("1", "100", "200")]
    b_results = [_result("2", "999", "888")]
    assert find_common_races(a_results, b_results) == []
