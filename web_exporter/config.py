"""Configuration management for web_exporter.

Handles loading/saving qbit_config.json with validation and type-safe defaults.
"""

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Optional

# ──────────────── Constants ────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP_DIR = os.path.join(BASE_DIR, "tmp")
CONFIG_FILE = os.path.join(BASE_DIR, "qbit_config.json")

DEFAULT_HOST = "http://127.0.0.1:8080"
DEFAULT_PORT = 6060
DEFAULT_QUEUE_NAME = "vmf"

# Ensure tmp directory exists
os.makedirs(TMP_DIR, exist_ok=True)


# ──────────────── Config Dataclass ────────────────
@dataclass
class QBitConfig:
    """Typed configuration for qBittorrent WebUI connection."""

    host: str = DEFAULT_HOST
    username: str = ""
    password: str = ""

    def validate(self) -> list[str]:
        """Return list of validation errors (empty = valid)."""
        errors = []
        if not self.host or not self.host.strip():
            errors.append("host is required")
        return errors


def load_config() -> QBitConfig:
    """Load config from qbit_config.json, returning defaults on failure."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return QBitConfig(
                host=data.get("host", DEFAULT_HOST),
                username=data.get("username", ""),
                password=data.get("password", ""),
            )
        except Exception:
            pass
    return QBitConfig()


def save_config(config: QBitConfig) -> None:
    """Save config to qbit_config.json (atomic write)."""
    tmp_path = CONFIG_FILE + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(asdict(config), f, indent=2)
    os.replace(tmp_path, CONFIG_FILE)


def config_from_dict(data: dict) -> QBitConfig:
    """Create QBitConfig from a dict (e.g. from request JSON)."""
    return QBitConfig(
        host=data.get("host", DEFAULT_HOST),
        username=data.get("username", ""),
        password=data.get("password", ""),
    )
