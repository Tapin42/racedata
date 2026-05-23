from __future__ import annotations

import re
import time
from datetime import datetime

from racedata.core.models import ScheduledEvent
from racedata.providers.rtrt.client import RtrtClient

RTRT_EVENTS_URL = "https://api.rtrt.me/events"
DEFAULT_EVENT_FIELDS = "name,date,desc,earliestStartTime,url"


def _extract_events_list(payload: object) -> list[dict]:
    if isinstance(payload, list):
        return [event for event in payload if isinstance(event, dict)]
    if isinstance(payload, dict):
        for key in ("list", "data", "events", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                return [event for event in value if isinstance(event, dict)]
    return []


def _event_date_in_past(event: dict, today: str) -> bool:
    event_date = event.get("date") or event.get("startDate")
    if not isinstance(event_date, str) or len(event_date) < 10:
        return False
    return event_date[:10] < today


def event_key_from_index_row(event: dict) -> str | None:
    for key in ("key", "eventKey", "event_key", "id", "eventId", "name"):
        value = event.get(key)
        if not isinstance(value, str) or not value:
            continue
        if key == "name":
            if value.upper().startswith("IRM-"):
                return value
            continue
        return value

    for key in ("url", "href", "self"):
        value = event.get(key)
        if isinstance(value, str) and value:
            match = re.search(r"/events/([^/?#]+)", value)
            if match:
                return match.group(1)
    return None


def event_distance_from_key_or_name(key: str | None, name: str) -> str | None:
    normalized_key = (key or "").upper()
    normalized_name = name.upper()
    if "703" in normalized_key or "70.3" in normalized_name or "70 3" in normalized_name:
        return "70.3"
    if "140.6" in normalized_name or "140 6" in normalized_name:
        return "140.6"
    return None


def _parse_earliest_start_time(raw: object) -> int | None:
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def scheduled_event_from_index_row(event: dict) -> ScheduledEvent | None:
    event_key = event_key_from_index_row(event)
    if not event_key:
        return None

    raw_date = event.get("date") or event.get("startDate")
    if not isinstance(raw_date, str) or len(raw_date) < 10:
        return None

    display_name = str(
        event.get("desc")
        or event.get("eventName")
        or event.get("description")
        or event_key
    ).strip()
    return ScheduledEvent(
        event_key=event_key,
        display_name=display_name,
        date=raw_date[:10],
        earliest_start_time=_parse_earliest_start_time(event.get("earliestStartTime")),
        distance=event_distance_from_key_or_name(event_key, display_name),
    )


def list_upcoming_events(
    client: RtrtClient,
    *,
    fields: str = DEFAULT_EVENT_FIELDS,
    page_size: int = 50,
    stop_at_past: bool = True,
    sleep_seconds: float = 0.2,
) -> list[ScheduledEvent]:
    today = datetime.now().strftime("%Y-%m-%d")
    all_events: list[ScheduledEvent] = []
    next_start = 1
    max_pages = 500

    for _ in range(max_pages):
        payload = client.get_json(
            RTRT_EVENTS_URL,
            params={
                "fields": fields,
                "max": page_size,
                "start": next_start,
            },
        )
        rows = _extract_events_list(payload)
        if not rows:
            break

        info = payload.get("info", {}) if isinstance(payload, dict) else {}
        try:
            last_index = int(info.get("last", 0))
        except (TypeError, ValueError):
            last_index = 0

        for row in rows:
            if stop_at_past and _event_date_in_past(row, today):
                return all_events
            scheduled = scheduled_event_from_index_row(row)
            if scheduled is not None:
                all_events.append(scheduled)

        window = last_index - next_start + 1 if last_index >= next_start else 0
        if window < page_size:
            break

        next_start = last_index + 1
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)

    return all_events


def filter_ironman_703_events(events: list[ScheduledEvent]) -> list[ScheduledEvent]:
    filtered: list[ScheduledEvent] = []
    for event in events:
        event_key = event.event_key.upper()
        if not event_key.startswith("IRM-"):
            continue
        if event.distance == "70.3" or "703" in event_key:
            filtered.append(event)
    return filtered
