from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable
from urllib.parse import parse_qs, urlparse

SPORTSTATS_LEADERBOARD_PATTERN = re.compile(
    r"https?://(?:www\.)?sportstats\.one/event/(?P<slug>[^/]+)/leaderboard/(?P<rid>\d+)/?$",
    re.IGNORECASE,
)
CID_PATTERN = re.compile(r'\\"cid\\":\\"(?P<cid>\d+)\\"')
LBL_PATTERN = re.compile(r'\\"lbl\\":\\"(?P<lbl>[^\\"]+)\\"')
CHO_PATTERN = re.compile(r'\\"cho\\":\\"(?P<cho>[^\\"]*)\\"')
FC_PATTERN = re.compile(r'\\"fc\\":\\"(?P<fc>[^\\"]*)\\"')


@dataclass(frozen=True)
class CheckpointCol:
    cid: str
    label: str
    cho: str = "0"
    fc: str = ""

    @property
    def is_main(self) -> bool:
        return self.cho == "1"

    @property
    def is_finish_column(self) -> bool:
        return self.fc == "1"


@dataclass(frozen=True)
class ParsedSportstatsUrl:
    slug: str
    rid: str
    seed_profile_id: str | None = None
    seed_lookup_type: str = "pid"


@dataclass(frozen=True)
class SportstatsLinkResolution:
    slug: str
    rid: str
    cols: tuple[CheckpointCol, ...]
    event_title: str = ""
    race_title: str = ""
    seed_profile_id: str | None = None
    seed_lookup_type: str = "pid"


def parse_sportstats_url(url: str) -> ParsedSportstatsUrl | None:
    text = url.strip()
    parsed = urlparse(text)
    path_match = SPORTSTATS_LEADERBOARD_PATTERN.match(
        f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    )
    if not path_match:
        return None

    query = parse_qs(parsed.query)
    focus_values = query.get("focus", [])
    type_values = query.get("type", [])
    seed_profile_id = focus_values[0].strip() if focus_values else None
    seed_lookup_type = type_values[0].strip().lower() if type_values else "pid"
    if seed_lookup_type not in {"pid", "bib"}:
        seed_lookup_type = "pid"

    return ParsedSportstatsUrl(
        slug=path_match.group("slug"),
        rid=path_match.group("rid"),
        seed_profile_id=seed_profile_id or None,
        seed_lookup_type=seed_lookup_type,
    )


def extract_checkpoint_cols(html: str, *, rid: str) -> list[CheckpointCol]:
    marker = f'rid\\":{rid}'
    start = html.find(marker)
    if start < 0:
        start = 0
    window = html[start : start + 25000]
    seen: set[str] = set()
    cols: list[CheckpointCol] = []
    course_complete = False
    for match in CID_PATTERN.finditer(window):
        cid = match.group("cid")
        if cid in seen:
            continue
        snippet = window[match.start() : match.start() + 800]
        lbl_match = LBL_PATTERN.search(snippet)
        if not lbl_match:
            continue
        label = lbl_match.group("lbl")
        if course_complete and label.strip().lower() == "start":
            break
        cho_match = CHO_PATTERN.search(snippet)
        fc_match = FC_PATTERN.search(snippet)
        seen.add(cid)
        col = CheckpointCol(
            cid=cid,
            label=label,
            cho=cho_match.group("cho") if cho_match else "0",
            fc=fc_match.group("fc") if fc_match else "",
        )
        cols.append(col)
        if col.is_finish_column and label.strip().lower() == "finish":
            course_complete = True
    return cols


def _title_from_html(html: str) -> tuple[str, str]:
    title_match = re.search(r"<title>([^<]+)</title>", html, re.IGNORECASE)
    if not title_match:
        return "", ""
    title = title_match.group(1).strip()
    if " - " in title:
        event_part, race_part = title.split(" - ", 1)
        race_part = race_part.replace(" - SportStats", "").strip()
        return event_part.strip(), race_part.strip()
    return title, ""


def resolve_sportstats_link(
    url: str,
    *,
    fetch_html: Callable[[str], str],
) -> SportstatsLinkResolution:
    parsed = parse_sportstats_url(url)
    if not parsed:
        raise ValueError("Invalid Sportstats leaderboard URL")

    html = fetch_html(url)
    cols = extract_checkpoint_cols(html, rid=parsed.rid)
    event_title, race_title = _title_from_html(html)
    return SportstatsLinkResolution(
        slug=parsed.slug,
        rid=parsed.rid,
        cols=tuple(cols),
        event_title=event_title,
        race_title=race_title,
        seed_profile_id=parsed.seed_profile_id,
        seed_lookup_type=parsed.seed_lookup_type,
    )
