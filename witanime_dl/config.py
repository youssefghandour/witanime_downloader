"""
Config loader — reads config.yaml and exposes a single Config object.
Falls back to safe defaults if the file is missing or a key is absent.
"""

import os
import yaml

DEFAULTS = {
    "download_dir":       "./downloads",
    "browser":            "brave",
    "brave_path":         r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
    "preferred_provider": "mediafire",
    "js_wait":            6,
    "request_delay":      2,
    "page_timeout":       25,
    "output_file":        "episodes.txt",
    "aria2_file":         "episodes.aria2",
    "progress_file":      "progress.json",
    "start_episode":      1,
    "max_episode":        9999,
}

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")


class Config:
    def __init__(self, path: str = CONFIG_PATH):
        data = {}
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

        for key, default in DEFAULTS.items():
            setattr(self, key, data.get(key, default))

    def __repr__(self):
        return f"Config({vars(self)})"


# Singleton — import this everywhere
cfg = Config()
