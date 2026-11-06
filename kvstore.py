"""Where the team's work is saved: Supabase when connected, local files otherwise.

On Streamlit Community Cloud the local disk is wiped whenever the app restarts,
so without Supabase the team's filter edits, allowed events, and hand-added
events disappear. With SUPABASE_URL and SUPABASE_SERVICE_KEY set, they live in
the `app_settings` table (see sql/schema.sql) and survive restarts.

Each setting is one row: name -> JSON value.
"""
import json
import os
import time
from functools import lru_cache

from config import PROJECT_DIR

DATA = PROJECT_DIR / "data"
TTL = 20  # seconds; filters are read many times per page load
_cache: dict[str, tuple[float, object]] = {}


def is_connected() -> bool:
    return bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_KEY"))


@lru_cache(maxsize=1)
def client():
    from supabase import create_client
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def where() -> str:
    return "supabase" if is_connected() else "local"


def get(name: str, default=None):
    hit = _cache.get(name)
    if hit and time.time() - hit[0] < TTL:
        return hit[1]
    if is_connected():
        rows = client().table("app_settings").select("value").eq("name", name).limit(1).execute().data
        value = rows[0]["value"] if rows else default
    else:
        try:
            value = json.loads((DATA / f"{name}.json").read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            value = default
    _cache[name] = (time.time(), value)
    return value


def put(name: str, value) -> None:
    if is_connected():
        client().table("app_settings").upsert({"name": name, "value": value}, on_conflict="name").execute()
    else:
        DATA.mkdir(parents=True, exist_ok=True)
        (DATA / f"{name}.json").write_text(json.dumps(value, indent=2, default=str))
    _cache[name] = (time.time(), value)
