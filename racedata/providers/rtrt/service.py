from __future__ import annotations

from racedata.core.models import AthleteRef, Course, Race, SegmentSplit
from racedata.core.split_filter import (
    collapse_intermediate_splits,
    filter_splits_by_course,
    main_point_names_from_conf,
)
from racedata.core.timing import is_blocked_label, normalize_segment_rows
from racedata.providers.rtrt.client import RtrtClient
from racedata.providers.rtrt.points import (
    course_labels_from_conf,
    default_course_from_splits,
    list_courses_from_conf,
    pointorder_for_course,
)


class RtrtProvider:
    def __init__(self, client: RtrtClient) -> None:
        self.client = client
        self._conf_cache: dict[str, dict] = {}

    def fetch_conf(self, event_key: str) -> dict:
        if event_key not in self._conf_cache:
            url = f"https://api.rtrt.me/events/{event_key}/conf"
            self._conf_cache[event_key] = self.client.post(url)
        return self._conf_cache[event_key]

    def search_athletes(self, race: Race, query: str) -> list[AthleteRef]:
        query = (query or "").strip()
        if len(query) < 2:
            return []
        url = f"https://api.rtrt.me/events/{race.event_key}/profiles"
        payload = self.client.post(
            url,
            {
                "max": "100",
                "total": "1",
                "failonmax": "1",
                "search": query,
                "module": "0",
            },
        )
        return self._extract_entries(payload, limit=25)

    def fetch_profile(self, race: Race, profile_id: str) -> AthleteRef | None:
        url = f"https://api.rtrt.me/events/{race.event_key}/profiles/{profile_id}"
        payload = self.client.post(url, {"max": "5"})
        entries = self._extract_entries(payload, limit=1)
        return entries[0] if entries else None

    def fetch_raw_splits(
        self,
        race: Race,
        profile_id: str,
        *,
        entry_id: str | None = None,
    ) -> list[dict]:
        if profile_id:
            url = f"https://api.rtrt.me/events/{race.event_key}/profiles/{profile_id}/splits"
            payload = self.client.post(url, {"max": "200"})
            rows = self._extract_split_rows(payload)
            if rows:
                return rows

        if entry_id:
            url = f"https://api.rtrt.me/events/{race.event_key}/entries/{entry_id}/splits"
            payload = self.client.post(url, {"max": "200"})
            return self._extract_split_rows(payload)
        return []

    def fetch_splits(
        self,
        race: Race,
        profile_id: str,
        *,
        entry_id: str | None = None,
        course_id: str | None = None,
        collapse_intermediates: bool = True,
    ) -> list[SegmentSplit]:
        raw_rows = self.fetch_raw_splits(race, profile_id, entry_id=entry_id)
        if course_id is None and raw_rows:
            course_id = default_course_from_splits(raw_rows)

        normalized = [
            split
            for split in normalize_segment_rows(raw_rows, course_id=course_id)
            if not is_blocked_label(split.label)
        ]
        if not collapse_intermediates:
            return normalized

        conf = self.fetch_conf(race.event_key)
        allowed = main_point_names_from_conf(
            pointorder_for_course(conf, course_id),
            course_id=course_id,
        )
        return collapse_intermediate_splits(normalized, allowed_point_names=allowed or None)

    def list_courses(self, race: Race) -> list[Course]:
        conf = self.fetch_conf(race.event_key)
        return list_courses_from_conf(conf)

    def course_labels(self, race: Race) -> dict[str, str]:
        conf = self.fetch_conf(race.event_key)
        return course_labels_from_conf(conf)

    def fetch_finish_split_aliases(self, race: Race) -> set[str]:
        url = f"https://api.rtrt.me/events/{race.event_key}/points"
        payload = self.client.post(url, {"max": "300"})
        list_payload = payload.get("list", [])
        if not isinstance(list_payload, list):
            return set()

        aliases: set[str] = set()
        for item in list_payload:
            if not isinstance(item, dict) or not _is_truthy(item.get("isFinish")):
                continue
            for key in ("label", "name"):
                value = str(item.get(key) or "").strip()
                if value:
                    aliases.add(value)
        return aliases

    def fetch_category_splits(self, url: str, *, max_results: str = "2000") -> dict:
        return self.client.post(url, {"max": max_results})

    def detect_courses_in_splits(
        self,
        race: Race,
        profile_id: str,
        *,
        entry_id: str | None = None,
    ) -> list[str]:
        raw_rows = self.fetch_raw_splits(race, profile_id, entry_id=entry_id)
        courses: list[str] = []
        for row in raw_rows:
            course = row.get("course")
            if course and course not in courses:
                courses.append(course)
        return courses

    def _extract_split_rows(self, payload: dict) -> list[dict]:
        rows: list[dict] = []
        direct_splits = payload.get("splits")
        if isinstance(direct_splits, list):
            rows.extend(item for item in direct_splits if isinstance(item, dict))

        list_payload = payload.get("list")
        if isinstance(list_payload, list):
            for item in list_payload:
                if not isinstance(item, dict):
                    continue
                if item.get("time") and (
                    item.get("name")
                    or item.get("split")
                    or item.get("label")
                    or item.get("point")
                ):
                    rows.append(item)
                embedded = item.get("splits")
                if isinstance(embedded, list):
                    rows.extend(split for split in embedded if isinstance(split, dict))
        return rows

    def _extract_entries(self, payload: dict, *, limit: int | None = None) -> list[AthleteRef]:
        list_payload = payload.get("list", [])
        if not isinstance(list_payload, list):
            return []

        normalized: list[AthleteRef] = []
        for item in list_payload:
            if not isinstance(item, dict):
                continue
            entry_id = str(
                item.get("entry")
                or item.get("entry_id")
                or item.get("id")
                or item.get("i")
                or item.get("u")
                or item.get("pid")
                or ""
            ).strip()
            first_name = str(item.get("first") or item.get("firstname") or item.get("fname") or "").strip()
            last_name = str(item.get("last") or item.get("lastname") or item.get("lname") or "").strip()
            full_name = " ".join(part for part in (first_name, last_name) if part)
            name = str(item.get("name") or full_name).strip()
            bib = str(item.get("bib") or item.get("racebib") or "").strip()
            division = str(
                item.get("division")
                or item.get("agegroup")
                or item.get("category")
                or item.get("class")
                or ""
            ).strip()
            profile_id = str(
                item.get("pid") or item.get("profile") or item.get("profile_id") or ""
            ).strip()
            if not entry_id or not name:
                continue
            normalized.append(
                AthleteRef(
                    profile_id=profile_id,
                    entry_id=entry_id,
                    name=name,
                    bib=bib,
                    division=division,
                )
            )
            if limit is not None and len(normalized) >= limit:
                return normalized
        return normalized


def _is_truthy(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}
