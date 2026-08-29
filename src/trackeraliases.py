# Upload Assistant © 2025 Audionut & wastaken7 — Licensed under UAPL v1.0
from collections.abc import Iterable
from typing import Any


# Keep renamed tracker codes working in saved configs, WebUI jobs, CLI presets,
# and cached meta.json files. Values must be current tracker_class_map keys.
TRACKER_ALIASES = {
    "TAV": "THV",
}


def normalize_tracker_name(value: Any) -> str:
    """Return the current uppercase tracker code for a configured value."""
    tracker = str(value).strip().upper()
    return TRACKER_ALIASES.get(tracker, tracker)


def normalize_tracker_list(value: Any) -> list[str]:
    """Normalize and de-duplicate a string or iterable of tracker codes."""
    if isinstance(value, str):
        candidates: Iterable[Any] = value.split(',')
    elif isinstance(value, Iterable) and not isinstance(value, (bytes, dict)):
        candidates = value
    else:
        return []

    trackers: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        tracker = normalize_tracker_name(candidate)
        if tracker and tracker not in seen:
            trackers.append(tracker)
            seen.add(tracker)

    return trackers
