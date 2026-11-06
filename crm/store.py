"""Where client data lives.

SupabaseStore is used when SUPABASE_URL and SUPABASE_SERVICE_KEY are set (the
hosted app and the Gmail job). LocalStore keeps everything in data/crm.json and
is used for local runs and tests.

Tables (see crm/schema.sql):
  clients (id, name, email, company, client_type, created_at)
  deals   (id, client_id, title, stage, notes, created_at, updated_at)
  emails  (id, client_id, gmail_id, subject, received_at, snippet)
"""
import json
import os
import uuid
from datetime import datetime, timezone

from config import PROJECT_DIR

from crm.model import STAGES, UNSORTED, company_from, parse_sender, suggest_type


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class LocalStore:
    def __init__(self, path=None):
        self.path = path or PROJECT_DIR / "data" / "crm.json"

    def _load(self) -> dict:
        try:
            return json.loads(self.path.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            return {"clients": [], "deals": [], "emails": []}

    def _save(self, db: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(db, indent=1))

    def all(self) -> dict:
        return self._load()

    def insert(self, table: str, row: dict) -> dict:
        db = self._load()
        row = {"id": str(uuid.uuid4()), "created_at": now(), **row}
        db[table].append(row)
        self._save(db)
        return row

    def update(self, table: str, row_id: str, values: dict) -> None:
        db = self._load()
        for r in db[table]:
            if r["id"] == row_id:
                r.update(values)
        self._save(db)

    def delete(self, table: str, row_id: str) -> None:
        db = self._load()
        db[table] = [r for r in db[table] if r["id"] != row_id]
        self._save(db)


class SupabaseStore:
    def __init__(self, url: str, key: str):
        from supabase import create_client
        self.db = create_client(url, key)

    def all(self) -> dict:
        return {t: self.db.table(t).select("*").execute().data for t in ("clients", "deals", "emails")}

    def insert(self, table: str, row: dict) -> dict:
        return self.db.table(table).insert(row).execute().data[0]

    def update(self, table: str, row_id: str, values: dict) -> None:
        self.db.table(table).update(values).eq("id", row_id).execute()

    def delete(self, table: str, row_id: str) -> None:
        self.db.table(table).delete().eq("id", row_id).execute()


def get_store():
    url, key = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY")
    if url and key:
        return SupabaseStore(url, key)
    return LocalStore()


def is_connected() -> bool:
    return bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_KEY"))


# ---------- the one rule that turns emails into clients ----------
def record_email(store, sender: str, gmail_id: str, subject: str, received_at: str, snippet: str = "",
                 db: dict | None = None) -> str:
    """Log an email. A new sender becomes a client with an open deal at stage 1.

    Returns 'skipped' (already logged), 'new client', or 'logged'.
    """
    db = db if db is not None else store.all()
    if any(e.get("gmail_id") == gmail_id for e in db["emails"]):
        return "skipped"
    name, addr = parse_sender(sender)
    client = next((c for c in db["clients"] if c.get("email") == addr), None)
    result = "logged"
    if client is None:
        client = store.insert("clients", {"name": name, "email": addr, "company": company_from(addr),
                                          "client_type": suggest_type(addr)})
        db["clients"].append(client)
        if client["client_type"] != "Team member":
            deal = store.insert("deals", {"client_id": client["id"], "title": subject or "New inquiry",
                                          "stage": STAGES[0], "notes": "", "updated_at": now()})
            db["deals"].append(deal)
        result = "new client"
    row = store.insert("emails", {"client_id": client["id"], "gmail_id": gmail_id, "subject": subject,
                                  "received_at": received_at, "snippet": snippet[:300]})
    db["emails"].append(row)
    return result


def set_type(store, client_id: str, client_type: str) -> None:
    store.update("clients", client_id, {"client_type": client_type})


def set_stage(store, deal_id: str, stage: str) -> None:
    assert stage in STAGES, stage
    store.update("deals", deal_id, {"stage": stage, "updated_at": now()})


def add_client(store, name: str, email: str, client_type: str, deal_title: str, stage: str = STAGES[0]) -> dict:
    client = store.insert("clients", {"name": name, "email": email.lower(), "company": company_from(email),
                                      "client_type": client_type or UNSORTED})
    if deal_title:
        store.insert("deals", {"client_id": client["id"], "title": deal_title, "stage": stage,
                               "notes": "", "updated_at": now()})
    return client
