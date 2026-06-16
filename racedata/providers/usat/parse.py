from __future__ import annotations

import re

from racedata.lifetime.models import LifetimeAthleteProfile, LifetimeRaceResult

BASE_URL = "https://member.usatriathlon.org"

SEARCH_BLOCK_RE = re.compile(
    r'wire:click="redirectToAthleteResults\(\''
    + re.escape(BASE_URL)
    + r"/athletes/(\d+)/results'\)\".*?(?=wire:click=\"redirectToAthleteResults|$)",
    re.S,
)
RESULT_BLOCK_RE = re.compile(
    r'href="'
    + re.escape(BASE_URL)
    + r"/events/(\d+)/races/(\d+)/results\?result_id=(\d+)\">(.*?)</a>",
    re.S,
)
ORDINAL_RE = re.compile(r"(\d+)(?:st|nd|rd|th)", re.I)
AGE_RE = re.compile(r"(\d+)yrs")


def parse_finish_seconds(value: str | None) -> float | None:
    if not value:
        return None
    text = str(value).strip()
    parts = text.split(":")
    try:
        if len(parts) == 3:
            hours = float(parts[0])
            minutes = float(parts[1])
            seconds = float(parts[2])
        elif len(parts) == 2:
            hours = 0.0
            minutes = float(parts[0])
            seconds = float(parts[1])
        else:
            return None
    except ValueError:
        return None
    return hours * 3600 + minutes * 60 + seconds


def _parse_position(text: str) -> int | None:
    match = ORDINAL_RE.search(text)
    if not match:
        return None
    return int(match.group(1))


def _parse_ranking(block: str) -> float | None:
    ranking_match = re.search(
        r'<span class="whitespace-pre">.*?<span class="font-bold text-lg">(\d+)</span>'
        r'.*?<span class="font-thin op9">\.</span>.*?<span class="font-thin op9">(\d+)</span>',
        block,
        re.S,
    )
    if ranking_match:
        return float(f"{ranking_match.group(1)}.{ranking_match.group(2)}")
    compact = re.search(r"(\d{2,3})\.(\d{3})", block)
    if compact:
        return float(f"{compact.group(1)}.{compact.group(2)}")
    return None


def _strip_tags(value: str) -> str:
    return re.sub(r"<[^>]+>", " ", value)


def _clean_text(value: str) -> str:
    return " ".join(_strip_tags(value).split())


def _parse_name_from_search_block(block: str) -> tuple[str, str]:
    last_match = re.search(r'<span class="font-bold">([^<]+)</span>', block)
    first_match = re.search(
        r'<span class="font-bold">[^<]+</span>,\s*</span><span>([^<]+)</span>',
        block,
    )
    last_name = last_match.group(1).strip() if last_match else ""
    first_name = first_match.group(1).strip() if first_match else ""
    return first_name, last_name


def parse_search_page(html: str) -> list[LifetimeAthleteProfile]:
    profiles: list[LifetimeAthleteProfile] = []
    for match in SEARCH_BLOCK_RE.finditer(html):
        athlete_id = match.group(1)
        block = match.group(0)
        first_name, last_name = _parse_name_from_search_block(block)
        location_match = re.search(r'fa-map-marker-alt"></i>\s*([^<\n]+)', block)
        location = location_match.group(1).strip() if location_match else ""
        age_match = AGE_RE.search(block)
        age = int(age_match.group(1)) if age_match else None
        gender_match = re.search(
            r'<div class="w-16 text-center">([^<]+)</div>',
            block,
        )
        gender = gender_match.group(1).strip() if gender_match else ""
        display_name = f"{first_name} {last_name}".strip()
        profiles.append(
            LifetimeAthleteProfile(
                provider="usat",
                athlete_id=athlete_id,
                display_name=display_name,
                first_name=first_name,
                last_name=last_name,
                age=age,
                gender=gender,
                location=location,
            )
        )
    return profiles


def parse_profile_header(html: str, *, athlete_id: str) -> LifetimeAthleteProfile | None:
    name_match = re.search(r'class="text-2xl font-bold">([^<]+)', html)
    if not name_match:
        return None
    display_name = name_match.group(1).strip()
    parts = display_name.split(None, 1)
    first_name = parts[0] if parts else ""
    last_name = parts[1] if len(parts) > 1 else ""
    age_match = AGE_RE.search(html)
    age = int(age_match.group(1)) if age_match else None
    gender_match = re.search(
        r'Gender</span>\s*<span class="text-lg ">([^<]+)</span>',
        html,
        re.S,
    )
    gender = gender_match.group(1).strip() if gender_match else ""
    location_match = re.search(
        r'Location</span>\s*<span class="text-lg ">([^<]+)</span>',
        html,
        re.S,
    )
    location = location_match.group(1).strip() if location_match else ""
    return LifetimeAthleteProfile(
        provider="usat",
        athlete_id=athlete_id,
        display_name=display_name,
        first_name=first_name,
        last_name=last_name,
        age=age,
        gender=gender,
        location=location,
    )


def _parse_result_block(
    event_id: str,
    race_id: str,
    result_id: str,
    block: str,
    *,
    athlete_id: str,
) -> LifetimeRaceResult:
    position = _parse_position(block)
    event_match = re.search(
        r'class="block text-xl text-darkblue font-bold mb-1">\s*([^<]+?)\s*</span>',
        block,
        re.S,
    )
    event_name = event_match.group(1).strip() if event_match else ""
    date_match = re.search(
        r'<span class="flex items-center gap-x-4 text-sm">.*?<span class="">\s*([^<]+?)\s*</span>',
        block,
        re.S,
    )
    race_date = date_match.group(1).strip() if date_match else ""
    race_match = re.search(
        r'<span class="flex items-center gap-x-4 text-sm">.*?<span class="">\s*[^<]+?\s*</span>\s*'
        r'<span class="">\s*([^<]+?)\s*</span>',
        block,
        re.S,
    )
    race_name = race_match.group(1).strip() if race_match else ""
    time_match = re.search(
        r'<span class="block text-muted text-sm font-thin ">\s*([^<]+?)\s*</span>',
        block,
        re.S,
    )
    finish_time = time_match.group(1).strip() if time_match else ""
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
        ranking=_parse_ranking(block),
        finish_time=finish_time,
        finish_seconds=parse_finish_seconds(finish_time),
    )


def parse_results_page(html: str, *, athlete_id: str) -> list[LifetimeRaceResult]:
    results: list[LifetimeRaceResult] = []
    for event_id, race_id, result_id, block in RESULT_BLOCK_RE.findall(html):
        results.append(
            _parse_result_block(
                event_id,
                race_id,
                result_id,
                block,
                athlete_id=athlete_id,
            )
        )
    return results
