import json
import os
from typing import List

DATA_DIR = "data"
LOG_FILE = os.path.join(DATA_DIR, "log.json")


def _ensure_file():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            json.dump([], f)


def save_entry(entry: dict) -> None:
    """Append a single food log entry to log.json."""
    _ensure_file()
    entries = load_all()
    entries.append(entry)
    with open(LOG_FILE, "w") as f:
        json.dump(entries, f, indent=2)


def load_all() -> List[dict]:
    """Load all log entries, sorted by timestamp ascending."""
    _ensure_file()
    with open(LOG_FILE, "r") as f:
        entries = json.load(f)
    return sorted(entries, key=lambda e: e.get("timestamp", ""))


def delete_entry(timestamp_iso: str) -> None:
    """Remove an entry by its timestamp."""
    entries = load_all()
    entries = [e for e in entries if e.get("timestamp") != timestamp_iso]
    with open(LOG_FILE, "w") as f:
        json.dump(entries, f, indent=2)