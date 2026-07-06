"""Queue export logic.

Handles deduplication against processed_files.log and atomic file writes.
"""

import json
import os
from dataclasses import dataclass
from typing import Optional

from .config import TMP_DIR


@dataclass
class ExportResult:
    """Result of an export operation."""

    added: int = 0
    dupes: int = 0
    excluded: int = 0
    queue_name: str = ""
    queue_file: str = ""


def load_processed_set(queue_name: str) -> set[str]:
    """Load the set of already-processed file paths for this queue."""
    processed_file = os.path.join(TMP_DIR, f"{queue_name}_processed_files.log")
    if os.path.exists(processed_file):
        try:
            with open(processed_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    return set(json.loads(content))
        except Exception:
            pass
    return set()


def export_queue(
    torrents: list,
    queue_name: str,
    exclude_count: int = 0,
) -> ExportResult:
    """Export torrents to a queue log file with deduplication.

    Args:
        torrents: List of torrent objects (already filtered by QBitConnection.get_torrents).
        queue_name: Name prefix for the queue file (e.g. 'vmf' -> vmf_queue.log).
        exclude_count: Number of torrents already excluded by tracker filter (for reporting).

    Returns:
        ExportResult with counts.
    """
    queue_name = (queue_name or "vmf").strip() or "vmf"
    log_file = os.path.join(TMP_DIR, f"{queue_name}_queue.log")

    processed_data = load_processed_set(queue_name)

    queue_data = []
    seen_paths = set()
    added_count = 0
    dupe_count = 0

    for t in torrents:
        path = getattr(t, "content_path", None)
        if not path:
            path = os.path.join(
                getattr(t, "save_path", ""), getattr(t, "name", "")
            )
        path = os.path.abspath(path)

        if path in processed_data or path in seen_paths:
            dupe_count += 1
        else:
            queue_data.append(path)
            seen_paths.add(path)
            added_count += 1

    # Atomic write: write to temp then rename
    temp_log = log_file + ".tmp"
    with open(temp_log, "w", encoding="utf-8") as f:
        json.dump(queue_data, f, indent=4)
    os.replace(temp_log, log_file)

    return ExportResult(
        added=added_count,
        dupes=dupe_count,
        excluded=exclude_count,
        queue_name=queue_name,
        queue_file=log_file,
    )
