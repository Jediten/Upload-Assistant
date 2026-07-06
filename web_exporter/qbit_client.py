"""qBittorrent client wrapper.

Provides a clean interface for connecting and querying qBittorrent WebUI API.
Raises exceptions instead of returning mixed types.
"""

import urllib.parse
from typing import Optional

from qbittorrentapi import Client, LoginFailed

from .config import QBitConfig
from .filters import FilterParams, build_api_params


class QBitConnectionError(Exception):
    """Raised when qBittorrent connection fails."""

    pass


class QBitConnection:
    """Wrapper around qbittorrentapi.Client with clean error handling."""

    def __init__(self, config: QBitConfig):
        self._config = config
        self._client: Optional[Client] = None

    def connect(self) -> Client:
        """Connect (or reconnect) to qBittorrent. Raises QBitConnectionError on failure."""
        if not self._config.host:
            raise QBitConnectionError("Host is required")

        try:
            host = self._config.host
            parsed = urllib.parse.urlparse(host)
            host_str = parsed.netloc if parsed.scheme else host

            self._client = Client(
                host=host_str,
                username=self._config.username or "",
                password=self._config.password or "",
            )
            self._client.auth_log_in()
            return self._client
        except LoginFailed as e:
            raise QBitConnectionError(f"Login failed: {e}") from e
        except Exception as e:
            raise QBitConnectionError(str(e)) from e

    @property
    def client(self) -> Client:
        if self._client is None:
            return self.connect()
        return self._client

    def get_categories(self) -> list[str]:
        """Return sorted list of category names."""
        cats = self.client.torrents_categories()
        return sorted(cats.keys())

    def get_tags(self) -> list[str]:
        """Return sorted list of tags."""
        tags = self.client.torrents_tags()
        return sorted(tags)

    def get_trackers(self) -> list[str]:
        """Return sorted list of unique tracker hostnames from all torrents."""
        tracker_set = set()
        for t in self.client.torrents_info():
            tracker_url = getattr(t, "tracker", "") or ""
            if tracker_url:
                parsed = urllib.parse.urlparse(tracker_url)
                host = parsed.hostname
                if host:
                    tracker_set.add(host)
        return sorted(tracker_set)

    def get_torrents(self, filters: FilterParams) -> list:
        """Fetch torrents with API-level filtering, then apply local filters.

        Uses build_api_params() to push as much filtering to the API as possible,
        then applies local filters (tracker, tag, size, date, name) in Python.
        """
        from .filters import apply_local_filters

        api_params = build_api_params(filters)
        categories = filters.categories or []

        all_torrents = []

        if filters.category_mode == "include":
            # Include mode: fetch specific categories (or all)
            if not categories or "ALL_WITHOUT_CATEGORY" in categories:
                params = {k: v for k, v in api_params.items() if k != "category"}
                all_torrents = list(self.client.torrents_info(**params))
            else:
                for cat in categories:
                    params = dict(api_params)
                    params["category"] = cat
                    all_torrents.extend(self.client.torrents_info(**params))
        else:
            # Exclude mode: fetch ALL then remove selected categories
            params = {k: v for k, v in api_params.items() if k != "category"}
            all_torrents = list(self.client.torrents_info(**params))
            if categories:
                excluded_cats = set(categories)
                all_torrents = [
                    t for t in all_torrents
                    if (getattr(t, "category", "") or "") not in excluded_cats
                ]

        # Apply Python-side filters (tracker, tag, size, date, name)
        return apply_local_filters(all_torrents, filters)
