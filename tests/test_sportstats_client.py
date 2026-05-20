from racedata.providers.sportstats.client import SportstatsClient


def test_get_builds_query_and_api_key_header():
    client = SportstatsClient(api_key="test-key")
    captured: dict = {}

    def transport(url: str, *, headers: dict) -> dict:
        captured["url"] = url
        captured["headers"] = headers
        return {"ok": True}

    client._transport = transport  # type: ignore[method-assign]
    result = client.get("getsingleresult", {"rid": "146818", "potype": "pid", "poid": "486"})
    assert result == {"ok": True}
    assert "rid=146818" in captured["url"]
    assert captured["headers"]["X-API-Key"] == "test-key"


def test_get_sorted_results_omits_api_key():
    client = SportstatsClient(api_key="test-key")
    captured: dict = {}

    def transport(url: str, *, headers: dict) -> dict:
        captured["url"] = url
        captured["headers"] = headers
        return {"ok": True}

    client._transport = transport  # type: ignore[method-assign]
    client.get_sorted_results({"rid": "146818", "limit": "5"})
    assert "X-API-Key" not in captured["headers"]
