from racedata.core.models import Race
from racedata.providers.factory import provider_for_race
from racedata.providers.rtrt.service import RtrtProvider
from racedata.providers.sportstats.service import SportstatsProvider


def test_provider_for_race_rtrt():
    race = Race(event_key="EVENT", display_name="Race", provider="rtrt", app_id="app1")
    provider = provider_for_race(
        race,
        rtrt_credentials=type("Creds", (), {"app_id": "app1", "token": "tok"})(),
    )
    assert isinstance(provider, RtrtProvider)


def test_provider_for_race_sportstats():
    race = Race(event_key="146818", display_name="Race", provider="sportstats")
    provider = provider_for_race(race, sportstats_cols=())
    assert isinstance(provider, SportstatsProvider)
