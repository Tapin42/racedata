from __future__ import annotations

from racedata.core.models import AthleteRef, Course, Race, SegmentSplit
from racedata.core.timing import format_hhmmss, is_blocked_label
from racedata.providers.sportstats.client import SportstatsClient
from racedata.providers.sportstats.link import CheckpointCol


def _ms_to_seconds(value: object | None, *, allow_zero: bool = False) -> int | None:
    if value is None:
        return None
    try:
        ms = int(value)
    except (TypeError, ValueError):
        return None
    if ms < 0:
        return None
    if ms == 0 and not allow_zero:
        return None
    return ms // 1000


def _participant_name(participant: dict) -> str:
    first = str(participant.get("pnf") or "").strip()
    last = str(participant.get("pnl") or "").strip()
    if first or last:
        return " ".join(part for part in (first, last) if part)
    return str(participant.get("dn") or "").strip()


class SportstatsProvider:
    def __init__(
        self,
        client: SportstatsClient | object,
        *,
        cols: tuple[CheckpointCol, ...] = (),
        time_type: str = "chip",
    ) -> None:
        self.client = client
        self.cols = cols
        self.time_type = time_type
        self._col_by_cid = {col.cid: col for col in cols}

    def search_athletes(self, race: Race, query: str) -> list[AthleteRef]:
        query = (query or "").strip()
        if len(query) < 2:
            return []
        payload = self.client.get_sorted_results(
            {
                "rid": race.event_key,
                "querytext": query,
                "limit": "25",
                "sort": "overall",
                "timeType": self.time_type,
            }
        )
        participants = payload.get("participantData", [])
        if not isinstance(participants, list):
            return []
        return [self._athlete_from_participant(item) for item in participants if isinstance(item, dict)]

    def fetch_profile(self, race: Race, profile_id: str) -> AthleteRef | None:
        participant = self._fetch_participant(race, profile_id, lookup_type="pid")
        if not participant:
            return None
        return self._athlete_from_participant(participant)

    def fetch_splits(
        self,
        race: Race,
        profile_id: str,
        *,
        entry_id: str | None = None,
        course_id: str | None = None,
        collapse_intermediates: bool = True,
    ) -> list[SegmentSplit]:
        del entry_id, course_id, collapse_intermediates
        participant = self._fetch_participant(race, profile_id, lookup_type="pid")
        if not participant:
            return []
        return self._splits_from_participant(participant)

    def list_courses(self, race: Race) -> list[Course]:
        del race
        return []

    def course_labels(self, race: Race) -> dict[str, str]:
        del race
        return {}

    def _fetch_participant(
        self,
        race: Race,
        profile_id: str,
        *,
        lookup_type: str,
    ) -> dict | None:
        payload = self.client.get_single_result(
            {
                "rid": race.event_key,
                "potype": lookup_type,
                "poid": profile_id,
            }
        )
        participants = payload.get("participantData", [])
        if not isinstance(participants, list) or not participants:
            return None
        first = participants[0]
        return first if isinstance(first, dict) else None

    def _athlete_from_participant(self, participant: dict) -> AthleteRef:
        pid = str(participant.get("pid") or "")
        return AthleteRef(
            profile_id=pid,
            entry_id=pid,
            name=_participant_name(participant),
            bib=str(participant.get("bib") or ""),
            division=str(participant.get("pc") or ""),
        )

    def _splits_from_participant(self, participant: dict) -> list[SegmentSplit]:
        data = participant.get("data")
        if not isinstance(data, dict):
            return []

        clock_key = {"chip": "cd", "gun": "cdg", "agt": "agt"}.get(self.time_type, "cd")
        order = [col.cid for col in self.cols] if self.cols else sorted(data.keys(), key=str)
        splits: list[SegmentSplit] = []
        previous_clock: int | None = None

        for cid in order:
            col = self._col_by_cid.get(str(cid))
            if col and col.is_finish_column:
                continue
            row = data.get(cid)
            if not isinstance(row, dict):
                continue
            label = col.label if col else str(cid)
            if is_blocked_label(label):
                continue
            is_start = label.strip().lower() == "start"
            clock_seconds = _ms_to_seconds(row.get(clock_key), allow_zero=is_start)
            if clock_seconds is None:
                continue
            leg_seconds = _ms_to_seconds(row.get("st"))
            leg_time = format_hhmmss(leg_seconds) if leg_seconds is not None else None
            if leg_seconds is None and previous_clock is not None:
                leg_seconds = clock_seconds - previous_clock
                if leg_seconds >= 0:
                    leg_time = format_hhmmss(leg_seconds)
            splits.append(
                SegmentSplit(
                    segment_id=str(cid),
                    label=label,
                    clock_time=format_hhmmss(clock_seconds),
                    clock_seconds=clock_seconds,
                    leg_time=leg_time,
                    leg_seconds=leg_seconds if leg_seconds is not None and leg_seconds >= 0 else None,
                    is_intermediate=not (col.is_main if col else False),
                )
            )
            previous_clock = clock_seconds
        return splits
