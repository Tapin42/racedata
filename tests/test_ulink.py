from pathlib import Path

from racedata.providers.rtrt.ulink import (
    parse_embed_params,
    parse_ulink_html,
    parse_ulink_url,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_ulink_url_venice():
    url = "https://rtrt.me/ulink/IRMA/IRM-VENICE703-2026/tracker/RFX9NGWK/focus"
    event, pid = parse_ulink_url(url)
    assert event == "IRM-VENICE703-2026"
    assert pid == "RFX9NGWK"


def test_parse_ulink_url_usata():
    url = "https://rtrt.me/ulink/USATA/USAT-AGE_GROUP-2025/tracker/RSGAK5DC/focus"
    event, pid = parse_ulink_url(url)
    assert event == "USAT-AGE_GROUP-2025"
    assert pid == "RSGAK5DC"


def test_parse_ulink_url_multisport():
    url = "https://rtrt.me/ulink/SSA/SS-MULTISPORT-2026/tracker/RULDMH9Y/focus"
    event, pid = parse_ulink_url(url)
    assert event == "SS-MULTISPORT-2026"
    assert pid == "RULDMH9Y"


def test_parse_embed_params_from_html():
    html = (FIXTURES / "ulink_venice.html").read_text()
    app_id, event = parse_embed_params(html)
    assert app_id == "5824c5c948fd08c23a8b4567"
    assert event == "IRM-VENICE703-2026"


def test_parse_ulink_html_with_profile_id():
    html = (FIXTURES / "ulink_usata.html").read_text()
    resolution = parse_ulink_html(html, profile_id="RSGAK5DC")
    assert resolution is not None
    assert resolution.app_id == "5a58df14c9f3495b058b4571"
    assert resolution.event_key == "USAT-AGE_GROUP-2025"
    assert resolution.profile_id == "RSGAK5DC"
