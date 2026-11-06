"""Events you add by hand. Saved to Supabase (app_settings: custom_events) or data/custom_events.json."""
import uuid

import kvstore


def load() -> list[dict]:
    return list(kvstore.get("custom_events") or [])


def save(events: list[dict]) -> None:
    kvstore.put("custom_events", events)


def add(event: dict) -> list[dict]:
    events = load()
    events.append({**event, "custom_id": f"c-{uuid.uuid4().hex[:8]}"})
    save(events)
    return events


def remove(custom_id: str) -> list[dict]:
    events = [e for e in load() if e.get("custom_id") != custom_id]
    save(events)
    return events
