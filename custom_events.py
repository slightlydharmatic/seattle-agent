"""Events you add by hand. Saved to data/custom_events.json so they survive restarts."""
import json
import uuid

from config import PROJECT_DIR

PATH = PROJECT_DIR / "data" / "custom_events.json"


def load() -> list[dict]:
    try:
        return json.loads(PATH.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save(events: list[dict]) -> None:
    PATH.parent.mkdir(parents=True, exist_ok=True)
    PATH.write_text(json.dumps(events, indent=2))


def add(event: dict) -> list[dict]:
    events = load()
    events.append({**event, "custom_id": f"c-{uuid.uuid4().hex[:8]}"})
    save(events)
    return events


def remove(custom_id: str) -> list[dict]:
    events = [e for e in load() if e.get("custom_id") != custom_id]
    save(events)
    return events
