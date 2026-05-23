from datetime import datetime
from unittest.mock import MagicMock

from racedata.core.models import ScheduledEvent
from racedata.providers.rtrt.events import (
    event_distance_from_key_or_name,
    event_key_from_index_row,
    filter_ironman_703_events,
    list_upcoming_events,
    scheduled_event_from_index_row,
)


def test_event_key_from_index_row_prefers_irm_name_field():
    row = {"name": "IRM-VENICE703-2026", "desc": "IRONMAN 70.3 Venice-Jesolo"}
    assert event_key_from_index_row(row) == "IRM-VENICE703-2026"


def test_event_key_from_index_row_extracts_from_url():
    row = {"url": "https://api.rtrt.me/events/irm-wisconsin703-2026"}
    assert event_key_from_index_row(row) == "irm-wisconsin703-2026"


def test_event_distance_from_key_or_name():
    assert event_distance_from_key_or_name("IRM-VENICE703-2026", "IRONMAN 70.3 Venice") == "70.3"
    assert event_distance_from_key_or_name("IRM-WISCONSIN-2026", "Ironman 140.6 Wisconsin") == "140.6"


def test_scheduled_event_from_index_row():
    event = scheduled_event_from_index_row(
        {
            "name": "IRM-ROCKFORD703-2026",
            "desc": "IRONMAN 70.3 Rockford",
            "date": "2026-06-14",
            "earliestStartTime": "1749907200",
        }
    )
    assert event == ScheduledEvent(
        event_key="IRM-ROCKFORD703-2026",
        display_name="IRONMAN 70.3 Rockford",
        date="2026-06-14",
        earliest_start_time=1749907200,
        distance="70.3",
    )


def test_filter_ironman_703_events():
    events = [
        ScheduledEvent("IRM-VENICE703-2026", "Venice", "2026-05-18", distance="70.3"),
        ScheduledEvent("IRM-WISCONSIN-2026", "Wisconsin", "2026-09-07", distance="140.6"),
        ScheduledEvent("SS-MULTISPORT-2026", "Multisport", "2026-04-01", distance=None),
    ]
    assert [event.event_key for event in filter_ironman_703_events(events)] == [
        "IRM-VENICE703-2026"
    ]


def test_list_upcoming_events_stops_at_past_event(monkeypatch):
    client = MagicMock()
    client.get_json.side_effect = [
        {
            "list": [
                {
                    "name": "IRM-VENICE703-2026",
                    "desc": "Venice",
                    "date": "2026-05-25",
                },
                {
                    "name": "IRM-OLD703-2025",
                    "desc": "Old",
                    "date": "2025-01-01",
                },
            ],
            "info": {"last": 2},
        }
    ]
    monkeypatch.setattr(
        "racedata.providers.rtrt.events.datetime",
        MagicMock(now=lambda: datetime(2026, 5, 20)),
    )

    events = list_upcoming_events(client, sleep_seconds=0)

    assert len(events) == 1
    assert events[0].event_key == "IRM-VENICE703-2026"
    client.get_json.assert_called_once()
