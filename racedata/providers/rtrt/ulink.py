from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse

from racedata.providers.rtrt.client import RtrtClient, SessionCredentials

ULINK_PATTERN = re.compile(
    r"https?://(?:www\.)?rtrt\.me/ulink/[^/]+/(?P<event>[^/]+)/tracker/(?P<pid>[A-Z0-9]+)(?:/focus)?/?$",
    re.IGNORECASE,
)
EMBED_PATTERN = re.compile(
    r"embed\.js\?appid=(?P<appid>[a-f0-9]+)&event=(?P<event>[^&\"']+)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class UlinkResolution:
    app_id: str
    event_key: str
    profile_id: str
    org_prefix: str = ""


def parse_ulink_url(url: str) -> tuple[str, str] | None:
    match = ULINK_PATTERN.match(url.strip())
    if not match:
        return None
    return match.group("event"), match.group("pid")


def parse_embed_params(html: str) -> tuple[str, str] | None:
    match = EMBED_PATTERN.search(html)
    if not match:
        return None
    return match.group("appid"), match.group("event")


def parse_ulink_html(html: str, *, profile_id: str | None = None) -> UlinkResolution | None:
    embed = parse_embed_params(html)
    if not embed:
        return None
    app_id, event_key = embed
    return UlinkResolution(
        app_id=app_id,
        event_key=event_key,
        profile_id=profile_id or "",
    )


def resolve_ulink(client: RtrtClient, url: str) -> UlinkResolution:
    parsed = parse_ulink_url(url)
    if not parsed:
        raise ValueError("Invalid RTRT ulink URL")

    event_key, profile_id = parsed
    html = client.get(url)
    resolution = parse_ulink_html(html, profile_id=profile_id)
    if not resolution:
        raise ValueError("Could not parse app credentials from ulink page")
    if resolution.event_key != event_key:
        raise ValueError("Event key mismatch in ulink resolution")

    path_parts = [part for part in urlparse(url).path.split("/") if part]
    org_prefix = path_parts[1] if len(path_parts) >= 2 and path_parts[0] == "ulink" else ""

    return UlinkResolution(
        app_id=resolution.app_id,
        event_key=event_key,
        profile_id=profile_id,
        org_prefix=org_prefix,
    )


def credentials_for_ulink(resolution: UlinkResolution) -> SessionCredentials:
    env = SessionCredentials.from_env()
    if env:
        return env
    return SessionCredentials.new_session(resolution.app_id)
