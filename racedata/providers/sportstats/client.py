from __future__ import annotations

import json
import os
from typing import Callable
from urllib.parse import urlencode

import requests

PUBLIC_BASE = "https://public.sportstats.one"
DEFAULT_API_KEY = "Wk5cgF3bQh12Rfg81N9f2a077mqe1tP24br0MZBG"


class SportstatsClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        transport: Callable[[str, dict], dict] | None = None,
    ) -> None:
        self.api_key = (api_key or os.getenv("SPORTSTATS_API_KEY") or DEFAULT_API_KEY).strip()
        self._transport = transport or self._default_transport

    def get(self, path: str, params: dict[str, str], *, use_api_key: bool = True) -> dict:
        query = urlencode({key: value for key, value in params.items() if value is not None})
        url = f"{PUBLIC_BASE}/{path.lstrip('/')}?{query}"
        headers = {"X-API-Key": self.api_key} if use_api_key else {}
        payload = self._transport(url, headers=headers)
        if not payload.get("ok", True) and payload.get("error"):
            raise ValueError(str(payload.get("error")))
        return payload

    def get_sorted_results(self, params: dict[str, str]) -> dict:
        return self.get("getsortedresults", params, use_api_key=False)

    def get_single_result(self, params: dict[str, str]) -> dict:
        return self.get("getsingleresult", params, use_api_key=True)

    def _default_transport(self, url: str, headers: dict) -> dict:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        return response.json()
