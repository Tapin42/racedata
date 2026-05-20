import json
from pathlib import Path

from racedata.core.models import Race
from racedata.providers.sportstats.link import CheckpointCol
from racedata.providers.sportstats.service import SportstatsProvider

FIXTURES = Path(__file__).parent / "fixtures"

COLS = (
    CheckpointCol("447406", "Start", cho="0"),
    CheckpointCol("447407", "Run 0.3mi", cho="0"),
    CheckpointCol("447408", "Run1", cho="1"),
    CheckpointCol("447415", "Run2", cho="1"),
    CheckpointCol("447416", "Finish", cho="1", fc="1"),
)


class StubSportstatsClient:
    def __init__(self, responses: dict[str, dict]) -> None:
        self.responses = responses

    def get_sorted_results(self, params: dict[str, str]) -> dict:
        if "querytext" in params:
            return self.responses["search"]
        return self.responses.get("sorted", {"ok": True, "participantData": []})

    def get_single_result(self, params: dict[str, str]) -> dict:
        return self.responses["single"]


def test_search_athletes_returns_refs():
    search_payload = json.loads((FIXTURES / "sportstats_search.json").read_text())
    race = Race(event_key="146818", display_name="Test", provider="sportstats")
    provider = SportstatsProvider(StubSportstatsClient({"search": search_payload}), cols=COLS)
    results = provider.search_athletes(race, "navratil")
    assert len(results) == 1
    assert results[0].profile_id == "486"
    assert results[0].name == "Joe Navratil"
    assert results[0].bib == "486"


def test_fetch_profile_from_single_result():
    single_payload = json.loads((FIXTURES / "sportstats_single.json").read_text())
    race = Race(event_key="146818", display_name="Test", provider="sportstats")
    provider = SportstatsProvider(StubSportstatsClient({"single": single_payload}), cols=COLS)
    athlete = provider.fetch_profile(race, "486")
    assert athlete is not None
    assert athlete.name == "Joe Navratil"


def test_fetch_splits_maps_checkpoints():
    single_payload = json.loads((FIXTURES / "sportstats_single.json").read_text())
    race = Race(event_key="146818", display_name="Test", provider="sportstats")
    provider = SportstatsProvider(StubSportstatsClient({"single": single_payload}), cols=COLS)
    splits = provider.fetch_splits(race, "486", collapse_intermediates=False)
    labels = [split.label for split in splits]
    assert "Start" in labels
    assert "Run1" in labels
    assert "Run2" in labels
    assert "Finish" not in labels
    assert not any(split.label == "Run 0.3mi" and not split.is_intermediate for split in splits)
    run2 = next(split for split in splits if split.label == "Run2")
    assert run2.clock_seconds is not None
    assert run2.leg_seconds is not None
    distance = next(split for split in splits if split.label == "Run 0.3mi")
    assert distance.is_intermediate
