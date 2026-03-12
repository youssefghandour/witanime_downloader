"""
Progress state — save/load after every episode so runs can be safely interrupted.

State file (progress.json) tracks:
- Which episodes were collected successfully
- Which failed (so they can be retried)
- File sizes for total calculation
"""

import json
import os
from witanime_dl.config import cfg


def load() -> dict:
    """Load saved progress. Returns empty state if file doesn't exist."""
    if os.path.exists(cfg.progress_file):
        try:
            with open(cfg.progress_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"collected": {}, "failed": []}


def save(state: dict):
    """Save current progress to disk."""
    with open(cfg.progress_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def clear():
    """Delete the progress file (start fresh)."""
    if os.path.exists(cfg.progress_file):
        os.remove(cfg.progress_file)
        print(f"  Progress cleared: {cfg.progress_file}")
