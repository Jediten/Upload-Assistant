"""Filter pipeline for qBittorrent torrent queries.

Separates API-level filters (pushed to qBittorrent) from Python-side filters
(tracker exclusion, size, date, name pattern).
"""

import re
import urllib.parse
from dataclasses import dataclass, field
from typing import Optional


# All valid status_filter values for qBittorrent API
VALID_STATUS_FILTERS = [
    "all",
    "downloading",
    "seeding",
    "completed",
    "paused",
    "active",
    "inactive",
    "resumed",
    "stalled",
    "stalled_uploading",
    "stalled_downloading",
    "errored",
]

# Common sort fields
VALID_SORT_FIELDS = [
    "name",
    "size",
    "added_on",
    "completed_on",
    "ratio",
    "progress",
    "dlspeed",
    "upspeed",
    "num_seeds",
    "num_leechs",
    "priority",
]


@dataclass
class FilterParams:
    """All filter options — both API-level and Python-side."""

    # ── API-level filters ──
    status_filter: str = "all"         # qBit status_filter param
    categories: list[str] = field(default_factory=list)
    category_mode: str = "include"     # "include" or "exclude"
    tags: list[str] = field(default_factory=list)
    tag_mode: str = "include"          # "include" or "exclude"
    sort: str = "added_on"             # Sort field
    reverse: bool = False              # Reverse sort order
    limit: Optional[int] = None        # Max torrents from API

    # ── Python-side filters ──
    trackers: list[str] = field(default_factory=list)
    tracker_mode: str = "exclude"      # "include" or "exclude" (default exclude for backward compat)
    min_size: Optional[int] = None     # Bytes
    max_size: Optional[int] = None     # Bytes
    added_after: Optional[int] = None  # Unix timestamp
    name_pattern: Optional[str] = None # Regex or substring


def build_api_params(filters: FilterParams) -> dict:
    """Build kwargs dict for qbittorrentapi.Client.torrents_info().

    Only includes parameters supported by the API.
    Category is handled separately in QBitConnection.get_torrents() because
    the API only supports a single category per call.
    """
    params = {}

    if filters.status_filter and filters.status_filter != "all":
        params["status_filter"] = filters.status_filter

    # Tag: only use API-level filter in include mode with single tag
    if filters.tags and len(filters.tags) == 1 and filters.tag_mode == "include":
        params["tag"] = filters.tags[0]

    if filters.sort:
        params["sort"] = filters.sort

    if filters.reverse:
        params["reverse"] = True

    if filters.limit and filters.limit > 0:
        params["limit"] = filters.limit

    return params


def filter_by_trackers(torrents: list, tracker_hosts: list[str], mode: str = "exclude") -> list:
    """Filter torrents by tracker hostname.

    mode='exclude': remove torrents matching tracker_hosts
    mode='include': keep only torrents matching tracker_hosts
    """
    if not tracker_hosts:
        return torrents

    host_set = set(tracker_hosts)
    result = []
    for t in torrents:
        tracker_url = getattr(t, "tracker", "") or ""
        host = ""
        if tracker_url:
            parsed = urllib.parse.urlparse(tracker_url)
            host = parsed.hostname or ""

        if mode == "include":
            if host in host_set:
                result.append(t)
        else:  # exclude
            if host not in host_set:
                result.append(t)
    return result


def filter_by_tags(torrents: list, tags: list[str], mode: str = "include") -> list:
    """Filter torrents by tags.

    mode='include': keep only torrents that have at least one of the given tags
    mode='exclude': remove torrents that have any of the given tags
    """
    if not tags:
        return torrents

    tag_set = set(tags)
    result = []
    for t in torrents:
        torrent_tags = set((getattr(t, "tags", "") or "").split(", ")) - {""}
        has_match = bool(torrent_tags & tag_set)

        if mode == "include":
            if has_match:
                result.append(t)
        else:  # exclude
            if not has_match:
                result.append(t)
    return result


def filter_by_size(
    torrents: list, min_size: Optional[int] = None, max_size: Optional[int] = None
) -> list:
    """Filter torrents by size range (bytes)."""
    if min_size is None and max_size is None:
        return torrents

    result = []
    for t in torrents:
        size = getattr(t, "size", 0) or 0
        if min_size is not None and size < min_size:
            continue
        if max_size is not None and size > max_size:
            continue
        result.append(t)
    return result


def filter_by_date(torrents: list, added_after: Optional[int] = None) -> list:
    """Keep only torrents added after the given unix timestamp."""
    if added_after is None:
        return torrents

    result = []
    for t in torrents:
        added_on = getattr(t, "added_on", 0) or 0
        if added_on >= added_after:
            result.append(t)
    return result


def filter_by_name(torrents: list, name_pattern: Optional[str] = None) -> list:
    """Filter torrents whose name matches the pattern (substring or regex)."""
    if not name_pattern:
        return torrents

    try:
        regex = re.compile(name_pattern, re.IGNORECASE)
    except re.error:
        # Fall back to literal substring match
        regex = re.compile(re.escape(name_pattern), re.IGNORECASE)

    result = []
    for t in torrents:
        name = getattr(t, "name", "") or ""
        if regex.search(name):
            result.append(t)
    return result


def apply_local_filters(torrents: list, filters: FilterParams) -> list:
    """Run the full Python-side filter pipeline.

    Called after API-level filtering is already applied.
    """
    torrents = filter_by_trackers(torrents, filters.trackers, filters.tracker_mode)
    # Tag filtering: if API didn't handle it (multi-tag or exclude mode)
    if filters.tags and (len(filters.tags) > 1 or filters.tag_mode == "exclude"):
        torrents = filter_by_tags(torrents, filters.tags, filters.tag_mode)
    torrents = filter_by_size(torrents, filters.min_size, filters.max_size)
    torrents = filter_by_date(torrents, filters.added_after)
    torrents = filter_by_name(torrents, filters.name_pattern)
    return torrents
