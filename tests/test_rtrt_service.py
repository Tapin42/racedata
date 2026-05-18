import json
from pathlib import Path

from racedata.core.models import Race
from racedata.providers.rtrt.points import course_labels_from_conf, list_courses_from_conf
from racedata.providers.rtrt.service import RtrtProvider

FIXTURES = Path(__file__).parent / "fixtures"


class StubClient:
    def __init__(self, responses: dict[str, dict]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, dict | None]] = []

    def register_session(self) -> None:
        return None

    def post(self, url: str, payload: dict | None = None) -> dict:
        self.calls.append((url, payload))
        for key, value in self.responses.items():
            if key in url:
                return value
        raise KeyError(url)


def test_extract_entries_from_profile_search():
    race = Race(event_key="EVENT", display_name="Race")
    client = StubClient(
        {
            "/profiles": {
                "list": [
                    {
                        "i": "e1",
                        "pid": "P1",
                        "fname": "Kiel",
                        "lname": "Bur",
                        "bib": "130",
                        "class": "M40-44",
                    }
                ]
            }
        }
    )
    provider = RtrtProvider(client)
    rows = provider.search_athletes(race, "kiel")
    assert len(rows) == 1
    assert rows[0].name == "Kiel Bur"
    assert rows[0].profile_id == "P1"


def test_fetch_splits_normalizes_list_payload():
    race = Race(event_key="EVENT", display_name="Race")
    splits_payload = json.loads((FIXTURES / "usat_olympic_splits.json").read_text())
    conf_payload = json.loads((FIXTURES / "usat_olympic_conf.json").read_text())
    client = StubClient(
        {
            "/profiles/RSGAK5DC/splits": splits_payload,
            "/conf": conf_payload,
        }
    )
    provider = RtrtProvider(client)
    splits = provider.fetch_splits(
        race,
        "RSGAK5DC",
        course_id="tri_olympic",
    )
    labels = [split.label for split in splits]
    assert "Swim" in labels
    assert "Finish" in labels


def test_course_labels_from_multisport_conf():
    conf = json.loads((FIXTURES / "multisport_conf.json").read_text())
    labels = course_labels_from_conf(conf)
    assert labels.get("route_5") == "Super Sprint Du"
    courses = list_courses_from_conf(conf)
    assert any(course.id == "route_5" for course in courses)
