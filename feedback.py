"""Thumbs up / thumbs down on events, and how they flow back into the classifier.

Each vote is stored with the event's text and what the model said about it,
so it can be used three ways:
  1. Override: a downvoted event is hidden right away; an upvoted one is kept.
  2. Few-shot examples: recent votes go into the classifier's prompt.
  3. Evaluation: votes are the labels for measuring precision and recall.

Saved to Supabase table `feedback` when SUPABASE_URL / SUPABASE_SERVICE_KEY are
set (see crm/schema.sql), otherwise to data/feedback.json.
"""
import json
import os
from datetime import datetime, timezone

from config import PROJECT_DIR

PATH = PROJECT_DIR / "data" / "feedback.json"
FIELDS = ("title", "description", "venue", "neighborhood", "cost", "category", "source")


def _supabase():
    url, key = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY")
    if not (url and key):
        return None
    from supabase import create_client
    return create_client(url, key).table("feedback")


def load() -> list[dict]:
    table = _supabase()
    if table is not None:
        return table.select("*").order("created_at").execute().data
    try:
        return json.loads(PATH.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_local(rows: list[dict]) -> None:
    PATH.parent.mkdir(parents=True, exist_ok=True)
    PATH.write_text(json.dumps(rows, indent=1, default=str))


def vote(event: dict, value: int, curation: dict | None = None, note: str = "") -> None:
    """Record +1 or -1 for an event. A new vote on the same event replaces the old one."""
    assert value in (1, -1)
    row = {
        "event_key": event["key"],
        "vote": value,
        "note": note,
        **{f: str(event.get(f) or "")[:500] for f in FIELDS},
        "model_score": (curation or {}).get("score"),
        "model_intent": (curation or {}).get("intent"),
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    table = _supabase()
    if table is not None:
        table.upsert(row, on_conflict="event_key").execute()
        return
    rows = [r for r in load() if r["event_key"] != row["event_key"]] + [row]
    _save_local(rows)


def clear(event_key: str) -> None:
    table = _supabase()
    if table is not None:
        table.delete().eq("event_key", event_key).execute()
        return
    _save_local([r for r in load() if r["event_key"] != event_key])


def votes_by_key(rows: list[dict] | None = None) -> dict[str, int]:
    return {r["event_key"]: int(r["vote"]) for r in (load() if rows is None else rows)}


def few_shots(rows: list[dict] | None = None, n_down: int = 8, n_up: int = 4) -> list[dict]:
    """The examples the classifier sees: the most recent downvotes and upvotes."""
    rows = load() if rows is None else rows
    rows = sorted(rows, key=lambda r: r.get("created_at") or "")
    down = [r for r in rows if int(r["vote"]) < 0][-n_down:]
    up = [r for r in rows if int(r["vote"]) > 0][-n_up:]
    return down + up


def few_shot_text(examples: list[dict]) -> str:
    if not examples:
        return ""
    lines = ["The Seattle Unlocked team reviewed these past events. Follow their judgment on similar events:"]
    for r in examples:
        verdict = "DO NOT FEATURE" if int(r["vote"]) < 0 else "FEATURE"
        why = f" Team note: {r['note']}." if r.get("note") else ""
        desc = (r.get("description") or "")[:160]
        lines.append(f'- {verdict}: "{r["title"]}" at {r.get("venue") or "unknown venue"}. {desc}{why}')
    return "\n".join(lines)
