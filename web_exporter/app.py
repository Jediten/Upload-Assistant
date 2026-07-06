"""Flask application factory and route registration.

This is the main entry point for the web_exporter package.
Run with: python -m web_exporter
   or:    python web_exporter/app.py
"""

import atexit
import os
import signal
import sys

# Allow running directly: python web_exporter/app.py
if __name__ == "__main__" or __package__ is None:
    _parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _parent not in sys.path:
        sys.path.insert(0, _parent)
    __package__ = "web_exporter"

from flask import Flask, Response, render_template, request, jsonify

from .config import (
    load_config,
    save_config,
    config_from_dict,
    DEFAULT_PORT,
    DEFAULT_QUEUE_NAME,
)
from .qbit_client import QBitConnection, QBitConnectionError
from .filters import FilterParams, VALID_STATUS_FILTERS, VALID_SORT_FIELDS
from .export import export_queue
from .runner import UploadRunner


# ──────────────── App Setup ────────────────

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static",
)

runner = UploadRunner()

# Cleanup on exit
atexit.register(runner.cleanup)

for sig in (signal.SIGTERM, signal.SIGINT):
    try:
        signal.signal(sig, lambda *_: (runner.cleanup(), sys.exit(0)))
    except (ValueError, OSError):
        pass


# ──────────────── Helper ────────────────

def _connect_qbit():
    """Create QBitConnection from saved config. Returns (connection, error_str)."""
    config = load_config()
    conn = QBitConnection(config)
    try:
        conn.connect()
        return conn, None
    except QBitConnectionError as e:
        return None, str(e)


# ──────────────── Routes ────────────────

@app.route("/")
def index():
    config = load_config()
    conn, err = _connect_qbit()

    categories = []
    tags = []
    trackers = []
    qbit_status = "Chưa kết nối"

    if conn is not None:
        qbit_status = "OK"
        try:
            categories = conn.get_categories()
        except Exception as e:
            qbit_status = f"Lỗi lấy Category: {e}"
        try:
            tags = conn.get_tags()
        except Exception:
            pass
        try:
            trackers = conn.get_trackers()
        except Exception:
            pass
    elif err:
        qbit_status = f"Lỗi: {err}"

    has_config = bool(config.host)

    return render_template(
        "index.html",
        config=config,
        has_config=has_config,
        qbit_status=qbit_status,
        categories=categories,
        tags=tags,
        trackers=trackers,
        status_filters=VALID_STATUS_FILTERS,
        sort_fields=VALID_SORT_FIELDS,
    )


@app.route("/save_config", methods=["POST"])
def save_config_route():
    data = request.json
    cfg = config_from_dict(data)
    save_config(cfg)
    return jsonify({"status": "success"})


@app.route("/test_api", methods=["POST"])
def test_api():
    data = request.json
    cfg = config_from_dict(data)
    conn = QBitConnection(cfg)
    try:
        conn.connect()
        cats = conn.get_categories()
        return jsonify({"status": "ok", "cats_count": len(cats)})
    except QBitConnectionError as e:
        return jsonify({"status": "error", "error": str(e)})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})


@app.route("/api/filters")
def api_filters():
    """Return metadata for dynamic filter UI (categories, tags, trackers, etc.)."""
    conn, err = _connect_qbit()
    if conn is None:
        return jsonify({"error": err or "Not connected"}), 500

    try:
        return jsonify({
            "categories": conn.get_categories(),
            "tags": conn.get_tags(),
            "trackers": conn.get_trackers(),
            "status_filters": VALID_STATUS_FILTERS,
            "sort_fields": VALID_SORT_FIELDS,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/export", methods=["POST"])
def export_route():
    data = request.json
    queue_name = (data.get("queue_name", DEFAULT_QUEUE_NAME) or DEFAULT_QUEUE_NAME).strip()

    # Build FilterParams from request
    filters = FilterParams(
        status_filter=data.get("status_filter", "all"),
        categories=data.get("categories", []),
        category_mode=data.get("category_mode", "include"),
        tags=data.get("tags", []),
        tag_mode=data.get("tag_mode", "include"),
        sort=data.get("sort", "added_on"),
        reverse=bool(data.get("reverse", False)),
        limit=int(data["limit"]) if data.get("limit") else None,
        trackers=data.get("trackers", []),
        tracker_mode=data.get("tracker_mode", "exclude"),
        min_size=int(data["min_size"]) if data.get("min_size") else None,
        max_size=int(data["max_size"]) if data.get("max_size") else None,
        added_after=int(data["added_after"]) if data.get("added_after") else None,
        name_pattern=data.get("name_pattern") or None,
    )

    # Legacy: handle "only_completed" checkbox
    if data.get("only_completed", False):
        filters.status_filter = "completed"

    # Validate: in include mode, categories are required
    if filters.category_mode == "include" and not filters.categories:
        return jsonify({"error": "Chưa chọn Category"}), 400

    conn, err = _connect_qbit()
    if conn is None:
        return jsonify({"error": f"Không thể kết nối qBittorrent: {err}"}), 500

    try:
        torrents = conn.get_torrents(filters)

        result = export_queue(torrents, queue_name)
        return jsonify({
            "status": "success",
            "added": result.added,
            "dupes": result.dupes,
            "excluded": result.excluded,
            "queue_name": result.queue_name,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/stream_upload")
def stream_upload():
    args_str = request.args.get("args", "")
    return Response(runner.stream_output(args_str), mimetype="text/event-stream")


@app.route("/upload_stdin", methods=["POST"])
def upload_stdin():
    data = request.get_json(silent=True) or {}
    line = data.get("data", "")
    if not isinstance(line, str):
        line = str(line)
    try:
        runner.send_stdin(line)
        return jsonify({"status": "ok"})
    except RuntimeError as e:
        return jsonify({"status": "error", "error": str(e)}), 400
    except (BrokenPipeError, OSError, ValueError) as e:
        return jsonify({"status": "error", "error": str(e)}), 400


@app.route("/stop_upload", methods=["POST"])
def stop_upload():
    stopped = runner.stop()
    return jsonify({"status": "stopped", "info": "stopped" if stopped else "no_process"})


@app.route("/run_upload_detached", methods=["POST"])
def run_upload_detached():
    data = request.json or {}
    args_str = data.get("args", "")
    try:
        runner.start_detached(args_str)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


# ──────────────── Entry Point ────────────────

def main():
    print("🚀 Giao diện WebUI Đang Chạy!")
    print(f"Vui lòng mở Trình duyệt Web và truy cập vào: http://127.0.0.1:{DEFAULT_PORT}")
    print("-----------------------------------------------------------------")

    import logging
    log = logging.getLogger("werkzeug")
    log.setLevel(logging.ERROR)

    app.run(host="127.0.0.1", port=DEFAULT_PORT, debug=False)


if __name__ == "__main__":
    main()
