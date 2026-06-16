from __future__ import annotations

from racedata.lifetime.models import HeadToHeadMatch, LifetimeRaceResult


def find_common_races(
    results_a: list[LifetimeRaceResult],
    results_b: list[LifetimeRaceResult],
) -> list[HeadToHeadMatch]:
    index_a = {(r.event_id, r.race_id): r for r in results_a}
    index_b = {(r.event_id, r.race_id): r for r in results_b}
    common_keys = set(index_a) & set(index_b)
    matches: list[HeadToHeadMatch] = []
    for key in common_keys:
        result_a = index_a[key]
        result_b = index_b[key]
        matches.append(
            HeadToHeadMatch(
                event_id=result_a.event_id,
                race_id=result_a.race_id,
                event_name=result_a.event_name,
                race_name=result_a.race_name,
                race_date=result_a.race_date,
                result_a=result_a,
                result_b=result_b,
            )
        )
    matches.sort(key=lambda match: match.race_date, reverse=True)
    return matches
