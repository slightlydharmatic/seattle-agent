"""The latest live fetch, saved to snapshots/latest.json.

The public page reads this file, so visitors never trigger paid API calls.
A weekly GitHub Action (and the team's Run button) refreshes it.
"""
import json
from datetime import date, datetime, timezone

from config import PROJECT_DIR

PATH = PROJECT_DIR / "snapshots" / "latest.json"
KEEP = ("events_raw", "pages", "source_urls", "pages_failed", "query", "curation")


def save(raw: dict) -> dict:
    snap = {k: raw.get(k) for k in KEEP}
    snap["fetched_at"] = datetime.now(timezone.utc).isoformat(timespec="minutes")
    PATH.parent.mkdir(parents=True, exist_ok=True)
    PATH.write_text(json.dumps(snap, indent=1, default=str))
    return snap


def load() -> dict | None:
    """Return the saved fetch, or None if there isn't one yet."""
    try:
        snap = json.loads(PATH.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    return snap if snap.get("events_raw") is not None else None


def fetched_on(snap: dict) -> date | None:
    try:
        return datetime.fromisoformat(snap["fetched_at"]).date()
    except (KeyError, ValueError, TypeError):
        return None
