"""Check the Supabase connection before relying on it.

    python check_supabase.py

Reads SUPABASE_URL and SUPABASE_SERVICE_KEY from .env, makes sure both tables
exist, writes and deletes one test row, and copies any local data up once.
Never prints the key.
"""
import json
import sys

import kvstore

if not kvstore.is_connected():
    sys.exit("Not connected: add SUPABASE_URL and SUPABASE_SERVICE_KEY to .env first.")

db = kvstore.client()
for table in ("feedback", "app_settings"):
    try:
        db.table(table).select("*").limit(1).execute()
        print(f"OK   table {table} is reachable")
    except Exception as err:
        msg = str(err)
        hint = ("run sql/schema.sql in the SQL editor" if "does not exist" in msg or "PGRST205" in msg
                else "check the URL and that the key is the service_role / secret key")
        sys.exit(f"FAIL table {table}: {msg[:160]}\n     Fix: {hint}")

db.table("app_settings").upsert({"name": "_check", "value": {"ok": True}}, on_conflict="name").execute()
db.table("app_settings").delete().eq("name", "_check").execute()
print("OK   write and delete work")

# One-time copy of anything saved locally, so nothing is lost when switching.
moved = []
for name in ("filters", "custom_events"):
    f = kvstore.DATA / f"{name}.json"
    if f.exists() and not db.table("app_settings").select("name").eq("name", name).execute().data:
        kvstore.put(name, json.loads(f.read_text()))
        moved.append(name)
f = kvstore.DATA / "feedback.json"
if f.exists():
    rows = json.loads(f.read_text())
    if rows:
        db.table("feedback").upsert(rows, on_conflict="event_key").execute()
        moved.append(f"{len(rows)} votes")
print("OK   copied up from this computer: " + (", ".join(moved) if moved else "nothing to copy"))
print("\nSupabase is connected. Votes, filters, and added events now survive restarts.")
