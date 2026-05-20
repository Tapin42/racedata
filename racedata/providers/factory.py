from __future__ import annotations

from racedata.core.models import Race
from racedata.core.protocol import TimingProvider
from racedata.providers.rtrt.client import RtrtClient, SessionCredentials
from racedata.providers.rtrt.service import RtrtProvider
from racedata.providers.sportstats.client import SportstatsClient
from racedata.providers.sportstats.link import CheckpointCol
from racedata.providers.sportstats.service import SportstatsProvider


def provider_for_race(
    race: Race,
    *,
    rtrt_credentials: SessionCredentials | None = None,
    sportstats_cols: tuple[CheckpointCol, ...] = (),
    sportstats_client: SportstatsClient | None = None,
) -> TimingProvider:
    if race.provider == "sportstats":
        client = sportstats_client or SportstatsClient()
        return SportstatsProvider(client, cols=sportstats_cols)
    app_id = race.app_id or (rtrt_credentials.app_id if rtrt_credentials else "")
    creds = rtrt_credentials or SessionCredentials.new_session(app_id or "placeholder")
    return RtrtProvider(RtrtClient(creds))
