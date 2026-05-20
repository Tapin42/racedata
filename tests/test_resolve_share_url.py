from pathlib import Path

import pytest

from racedata.core.models import Race
from racedata.providers.rtrt.client import SessionCredentials
from racedata.providers.rtrt.ulink import UlinkResolution
from racedata.resolve import resolve_share_url

FIXTURES = Path(__file__).parent / "fixtures"


class FakeRtrtClient:
    def get(self, url: str) -> str:
        if "venice" in url.lower() or "RFX9NGWK" in url:
            return (FIXTURES / "ulink_venice.html").read_text()
        return (FIXTURES / "ulink_multisport.html").read_text()


def test_resolve_sportstats_url_without_focus():
    html = (FIXTURES / "sportstats_leaderboard.html").read_text()
    url = "https://sportstats.one/event/usat-multisport/leaderboard/146818"

    resolution = resolve_share_url(url, fetch_html=lambda _url: html)
    assert resolution.provider == "sportstats"
    assert resolution.race.provider == "sportstats"
    assert resolution.race.event_key == "146818"
    assert resolution.race.display_name == "USA Triathlon Multisport"
    assert resolution.race_title == "Super Sprint Time Trial Duathlon"
    assert resolution.seed_profile_id is None
    assert resolution.credentials is None
    assert len(resolution.checkpoint_cols) > 0


def test_resolve_sportstats_url_with_focus():
    html = (FIXTURES / "sportstats_leaderboard.html").read_text()
    url = "https://sportstats.one/event/usat-multisport/leaderboard/146818?focus=486&type=pid"

    resolution = resolve_share_url(url, fetch_html=lambda _url: html)
    assert resolution.seed_profile_id == "486"


def test_resolve_rtrt_ulink(monkeypatch):
    url = "https://rtrt.me/ulink/IRMA/IRM-VENICE703-2026/tracker/RFX9NGWK/focus"

    def fake_credentials(resolution: UlinkResolution) -> SessionCredentials:
        return SessionCredentials(app_id=resolution.app_id, token="TESTTOKEN")

    monkeypatch.setattr(
        "racedata.resolve.credentials_for_ulink",
        fake_credentials,
    )
    resolution = resolve_share_url(url, rtrt_client=FakeRtrtClient())
    assert resolution.provider == "rtrt"
    assert resolution.race.event_key == "IRM-VENICE703-2026"
    assert resolution.seed_profile_id == "RFX9NGWK"
    assert resolution.credentials is not None
    assert resolution.credentials.app_id == "5824c5c948fd08c23a8b4567"


def test_resolve_invalid_url_raises():
    with pytest.raises(ValueError, match="Unsupported"):
        resolve_share_url("https://example.com/not-a-race")
