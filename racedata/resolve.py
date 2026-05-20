from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from racedata.core.models import Race
from racedata.providers.rtrt.client import RtrtClient, SessionCredentials
from racedata.providers.rtrt.ulink import (
    UlinkResolution,
    credentials_for_ulink,
    resolve_ulink,
)
from racedata.providers.sportstats.link import CheckpointCol, resolve_sportstats_link


@dataclass(frozen=True)
class ShareResolution:
    provider: str
    race: Race
    seed_profile_id: str | None = None
    seed_lookup_type: str = "pid"
    credentials: SessionCredentials | None = None
    checkpoint_cols: tuple[CheckpointCol, ...] = ()
    slug: str = ""
    event_title: str = ""
    race_title: str = ""


def resolve_share_url(
    url: str,
    *,
    rtrt_client: RtrtClient | object | None = None,
    fetch_html: Callable[[str], str] | None = None,
) -> ShareResolution:
    text = (url or "").strip()
    if "sportstats.one" in text.lower():
        fetcher = fetch_html
        if fetcher is None:
            import requests

            def fetcher(target: str) -> str:
                response = requests.get(target, timeout=20)
                response.raise_for_status()
                return response.text

        resolution = resolve_sportstats_link(text, fetch_html=fetcher)
        event_title = resolution.event_title or f"Race {resolution.rid}"
        race = Race(
            event_key=resolution.rid,
            display_name=event_title,
            provider="sportstats",
        )
        return ShareResolution(
            provider="sportstats",
            race=race,
            seed_profile_id=resolution.seed_profile_id,
            seed_lookup_type=resolution.seed_lookup_type,
            checkpoint_cols=resolution.cols,
            slug=resolution.slug,
            event_title=event_title,
            race_title=resolution.race_title,
        )

    if "rtrt.me" in text.lower():
        client = rtrt_client
        if client is None:
            placeholder = SessionCredentials.new_session("placeholder")
            client = RtrtClient(placeholder)
        ulink: UlinkResolution = resolve_ulink(client, text)
        creds = credentials_for_ulink(ulink)
        race = Race(
            event_key=ulink.event_key,
            display_name=ulink.event_key,
            provider="rtrt",
            app_id=ulink.app_id,
        )
        return ShareResolution(
            provider="rtrt",
            race=race,
            seed_profile_id=ulink.profile_id,
            credentials=creds,
        )

    raise ValueError("Unsupported share link URL")
