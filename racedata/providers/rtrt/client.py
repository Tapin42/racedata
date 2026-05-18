from __future__ import annotations

import os
import uuid
from dataclasses import dataclass

import requests

RTRT_BASE_PARAMS = {
    "timesort": "1",
    "nohide": "1",
    "checksum": "",
    "max": "200",
    "catloc": "1",
    "cattotal": "1",
    "units": "standard",
    "source": "webtracker",
}


@dataclass(frozen=True)
class SessionCredentials:
    app_id: str
    token: str

    @classmethod
    def from_env(cls) -> SessionCredentials | None:
        app_id = os.getenv("RTRT_APPID", "").strip()
        token = os.getenv("RTRT_TOKEN", "").strip()
        if app_id and token:
            return cls(app_id=app_id, token=token)
        return None

    @classmethod
    def new_session(cls, app_id: str) -> SessionCredentials:
        return cls(app_id=app_id, token=uuid.uuid4().hex.upper()[:20])


class RtrtClient:
    def __init__(self, credentials: SessionCredentials) -> None:
        self.credentials = credentials
        self._registered = False

    def register_session(self) -> None:
        if self._registered:
            return
        url = "https://api.rtrt.me/publicconf"
        data = {
            "appid": self.credentials.app_id,
            "token": self.credentials.token,
            "web": "1",
            "secure": "1",
            "version": "0",
            "app": "0",
        }
        response = requests.post(url, data=data, timeout=20)
        response.raise_for_status()
        self._registered = True

    def post(self, url: str, payload: dict | None = None) -> dict:
        self.register_session()
        data = RTRT_BASE_PARAMS.copy()
        data["appid"] = self.credentials.app_id
        data["token"] = self.credentials.token
        if payload:
            data.update(payload)
        response = requests.post(url, data=data, timeout=20)
        response.raise_for_status()
        result = response.json()
        if not isinstance(result, dict):
            raise RuntimeError("RTRT payload is not an object")
        return result

    def get(self, url: str, *, params: dict | None = None) -> str:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        return response.text
