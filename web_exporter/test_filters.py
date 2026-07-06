"""Smoke tests for web_exporter.filters module.

Tests the filter pipeline logic without needing a live qBittorrent connection.
Run with: python -m pytest web_exporter/test_filters.py -v
"""

import pytest
from types import SimpleNamespace

from web_exporter.filters import (
    FilterParams,
    build_api_params,
    filter_by_trackers,
    filter_by_tags,
    filter_by_size,
    filter_by_date,
    filter_by_name,
    apply_local_filters,
)


# ── Helpers ──

def _make_torrent(name="Test", size=1_000_000_000, tracker="https://tracker.example.com/announce", added_on=1700000000, tags=""):
    """Create a mock torrent object."""
    return SimpleNamespace(
        name=name,
        size=size,
        tracker=tracker,
        added_on=added_on,
        tags=tags,
        content_path=f"/downloads/{name}",
        save_path="/downloads",
    )


# ── build_api_params ──

class TestBuildApiParams:
    def test_default_filters_has_sort(self):
        f = FilterParams()
        params = build_api_params(f)
        assert params == {"sort": "added_on"}

    def test_status_filter(self):
        f = FilterParams(status_filter="completed")
        params = build_api_params(f)
        assert params["status_filter"] == "completed"
        assert "sort" in params

    def test_sort_and_reverse(self):
        f = FilterParams(sort="name", reverse=True)
        params = build_api_params(f)
        assert params["sort"] == "name"
        assert params["reverse"] is True

    def test_limit(self):
        f = FilterParams(limit=50)
        params = build_api_params(f)
        assert params["limit"] == 50

    def test_single_tag_include(self):
        f = FilterParams(tags=["movies"], tag_mode="include")
        params = build_api_params(f)
        assert params["tag"] == "movies"

    def test_multi_tag_not_in_api(self):
        f = FilterParams(tags=["movies", "tv"], tag_mode="include")
        params = build_api_params(f)
        assert "tag" not in params

    def test_tag_exclude_not_in_api(self):
        f = FilterParams(tags=["movies"], tag_mode="exclude")
        params = build_api_params(f)
        assert "tag" not in params


# ── exclude_trackers ──

class TestFilterByTrackers:
    def test_no_filter(self):
        torrents = [_make_torrent()]
        result = filter_by_trackers(torrents, [])
        assert len(result) == 1

    def test_exclude_matching(self):
        torrents = [
            _make_torrent(name="T1", tracker="https://tracker.example.com/announce"),
            _make_torrent(name="T2", tracker="https://other.example.com/announce"),
        ]
        result = filter_by_trackers(torrents, ["tracker.example.com"], mode="exclude")
        assert len(result) == 1
        assert result[0].name == "T2"

    def test_include_matching(self):
        torrents = [
            _make_torrent(name="T1", tracker="https://tracker.example.com/announce"),
            _make_torrent(name="T2", tracker="https://other.example.com/announce"),
        ]
        result = filter_by_trackers(torrents, ["tracker.example.com"], mode="include")
        assert len(result) == 1
        assert result[0].name == "T1"

    def test_exclude_all(self):
        torrents = [
            _make_torrent(tracker="https://a.com/announce"),
            _make_torrent(tracker="https://b.com/announce"),
        ]
        result = filter_by_trackers(torrents, ["a.com", "b.com"], mode="exclude")
        assert len(result) == 0

    def test_no_tracker_field(self):
        t = _make_torrent()
        t.tracker = ""
        result = filter_by_trackers([t], ["tracker.example.com"], mode="exclude")
        assert len(result) == 1


# ── filter_by_tags ──

class TestFilterByTags:
    def test_include_matching(self):
        torrents = [
            _make_torrent(name="T1", tags="movies, hd"),
            _make_torrent(name="T2", tags="tv"),
        ]
        result = filter_by_tags(torrents, ["movies"], mode="include")
        assert len(result) == 1
        assert result[0].name == "T1"

    def test_exclude_matching(self):
        torrents = [
            _make_torrent(name="T1", tags="movies, hd"),
            _make_torrent(name="T2", tags="tv"),
        ]
        result = filter_by_tags(torrents, ["movies"], mode="exclude")
        assert len(result) == 1
        assert result[0].name == "T2"

    def test_no_tags(self):
        torrents = [_make_torrent()]
        result = filter_by_tags(torrents, [])
        assert len(result) == 1


# ── filter_by_size ──

class TestFilterBySize:
    def test_no_filter(self):
        torrents = [_make_torrent(size=100)]
        assert len(filter_by_size(torrents)) == 1

    def test_min_size(self):
        torrents = [
            _make_torrent(name="small", size=100),
            _make_torrent(name="big", size=1000),
        ]
        result = filter_by_size(torrents, min_size=500)
        assert len(result) == 1
        assert result[0].name == "big"

    def test_max_size(self):
        torrents = [
            _make_torrent(name="small", size=100),
            _make_torrent(name="big", size=1000),
        ]
        result = filter_by_size(torrents, max_size=500)
        assert len(result) == 1
        assert result[0].name == "small"

    def test_range(self):
        torrents = [
            _make_torrent(name="tiny", size=10),
            _make_torrent(name="mid", size=500),
            _make_torrent(name="huge", size=10000),
        ]
        result = filter_by_size(torrents, min_size=100, max_size=1000)
        assert len(result) == 1
        assert result[0].name == "mid"


# ── filter_by_date ──

class TestFilterByDate:
    def test_no_filter(self):
        torrents = [_make_torrent()]
        assert len(filter_by_date(torrents)) == 1

    def test_after_filter(self):
        torrents = [
            _make_torrent(name="old", added_on=1600000000),
            _make_torrent(name="new", added_on=1700000000),
        ]
        result = filter_by_date(torrents, added_after=1650000000)
        assert len(result) == 1
        assert result[0].name == "new"


# ── filter_by_name ──

class TestFilterByName:
    def test_no_filter(self):
        torrents = [_make_torrent()]
        assert len(filter_by_name(torrents)) == 1

    def test_substring(self):
        torrents = [
            _make_torrent(name="Movie.1080p.BluRay"),
            _make_torrent(name="Movie.720p.WEB"),
        ]
        result = filter_by_name(torrents, "1080p")
        assert len(result) == 1
        assert "1080p" in result[0].name

    def test_regex(self):
        torrents = [
            _make_torrent(name="Movie.1080p.BluRay"),
            _make_torrent(name="Movie.720p.WEB"),
            _make_torrent(name="Show.2160p.HEVC"),
        ]
        result = filter_by_name(torrents, r"\d{4}p")
        # 1080p, 2160p match \d{4}p; 720p is only 3 digits before 'p'
        assert len(result) == 2

    def test_invalid_regex_fallback(self):
        torrents = [_make_torrent(name="test(123)")]
        # Invalid regex "(123" → falls back to literal match
        result = filter_by_name(torrents, "(123)")
        assert len(result) == 1


# ── apply_local_filters (pipeline) ──

class TestApplyLocalFilters:
    def test_full_pipeline(self):
        torrents = [
            _make_torrent(name="Movie.1080p", size=5_000_000_000, tracker="https://good.com/announce", added_on=1700000000),
            _make_torrent(name="Movie.720p", size=500_000_000, tracker="https://bad.com/announce", added_on=1700000000),
            _make_torrent(name="Old.1080p", size=5_000_000_000, tracker="https://good.com/announce", added_on=1600000000),
            _make_torrent(name="Tiny.1080p", size=100_000, tracker="https://good.com/announce", added_on=1700000000),
        ]
        filters = FilterParams(
            trackers=["bad.com"],
            tracker_mode="exclude",
            min_size=1_000_000,
            added_after=1650000000,
            name_pattern="1080p",
        )
        result = apply_local_filters(torrents, filters)
        assert len(result) == 1
        assert result[0].name == "Movie.1080p"
