import os
import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".downloader"
CONFIG_FILE = CONFIG_DIR / "config.json"
DB_FILE = CONFIG_DIR / "data.db"

DEFAULT_CONFIG = {
    "default_threads": 4,
    "default_download_path": str(Path.home() / "Downloads"),
    "chunk_size": 1024 * 1024,
    "max_retries": 3,
    "timeout": 30,
    "max_speed_kbps": 0,
    "checksum_type": None,
    "accent_color": "cyan",
    "notifications": True,
    "minimize_to_tray": True,
    "cookies_browser": "firefox",
    "naming_template": "%(title)s.%(ext)s",
    "auto_subtitles": False,
    "embed_subtitles": True,
    "scheduler_enabled": False,
    "scheduler_time": "02:00",
}


def load_config():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                return {**DEFAULT_CONFIG, **json.load(f)}
        except Exception:
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()


def save_config(config):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def get_db_path():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return str(DB_FILE)
