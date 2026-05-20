from pathlib import Path

from racedata.providers.sportstats.link import (
    extract_checkpoint_cols,
    parse_sportstats_url,
    resolve_sportstats_link,
)

FIXTURES = Path(__file__).parent / "fixtures"
LEADERBOARD_HTML = FIXTURES / "sportstats_leaderboard.html"


def test_parse_sportstats_url_basic():
    url = "https://sportstats.one/event/usat-multisport/leaderboard/146818"
    parsed = parse_sportstats_url(url)
    assert parsed is not None
    assert parsed.slug == "usat-multisport"
    assert parsed.rid == "146818"
    assert parsed.seed_profile_id is None
    assert parsed.seed_lookup_type == "pid"


def test_parse_sportstats_url_with_focus():
    url = "https://sportstats.one/event/usat-multisport/leaderboard/146818?focus=486&type=pid"
    parsed = parse_sportstats_url(url)
    assert parsed is not None
    assert parsed.seed_profile_id == "486"
    assert parsed.seed_lookup_type == "pid"


def test_parse_sportstats_url_with_bib_type():
    url = "https://sportstats.one/event/usat-multisport/leaderboard/146818?focus=101&type=bib"
    parsed = parse_sportstats_url(url)
    assert parsed is not None
    assert parsed.seed_profile_id == "101"
    assert parsed.seed_lookup_type == "bib"


def test_extract_checkpoint_cols_from_fixture():
    html = LEADERBOARD_HTML.read_text()
    cols = extract_checkpoint_cols(html, rid="146818")
    by_id = {col.cid: col for col in cols}
    assert by_id["447406"].label == "Start"
    assert by_id["447406"].cho == "0"
    assert by_id["447408"].label == "Run1"
    assert by_id["447408"].is_main
    assert by_id["447407"].label.startswith("Run 0.3")
    assert not by_id["447407"].is_main
    assert by_id["447416"].is_finish_column
    assert "447504" not in by_id


def test_resolve_sportstats_link_uses_fetcher():
    html = LEADERBOARD_HTML.read_text()
    url = "https://sportstats.one/event/usat-multisport/leaderboard/146818?focus=486&type=pid"

    resolution = resolve_sportstats_link(url, fetch_html=lambda _url: html)
    assert resolution.rid == "146818"
    assert resolution.slug == "usat-multisport"
    assert resolution.seed_profile_id == "486"
    assert len(resolution.cols) >= 10
