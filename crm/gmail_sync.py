"""Pull client emails from Gmail into the tracker.

    python -m crm.gmail_sync

Reads messages matching GMAIL_QUERY (default: label:Clients newer_than:30d).
Each new sender becomes a client with a deal at "Unconfirmed deal"; every
email is logged once. Read-only access to Gmail; nothing is sent or changed.

Needs:
  GMAIL_TOKEN_JSON   the token made by `python -m crm.gmail_auth` (one line of JSON)
  SUPABASE_URL, SUPABASE_SERVICE_KEY   (otherwise it writes to data/crm.json)
Optional:
  GMAIL_QUERY        which emails count as client emails
  GMAIL_SELF         your own addresses, comma separated, so they're skipped
  TEAM_EMAILS / TEAM_DOMAINS / LARGE_CLIENT_DOMAINS   type hints (see crm/model.py)
"""
import json
import os
import sys
from email.utils import parsedate_to_datetime

from dotenv import load_dotenv

from config import PROJECT_DIR

load_dotenv(PROJECT_DIR / ".env")

from crm.model import parse_sender  # noqa: E402
from crm.store import get_store, record_email  # noqa: E402

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def gmail_service():
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    raw = os.getenv("GMAIL_TOKEN_JSON")
    if not raw:
        raise RuntimeError("GMAIL_TOKEN_JSON is not set. Run `python -m crm.gmail_auth` once to create it.")
    creds = Credentials.from_authorized_user_info(json.loads(raw), SCOPES)
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def fetch(service, query: str, limit: int = 200) -> list[dict]:
    out, token = [], None
    while len(out) < limit:
        resp = service.users().messages().list(userId="me", q=query, pageToken=token, maxResults=100).execute()
        for m in resp.get("messages", []):
            msg = service.users().messages().get(
                userId="me", id=m["id"], format="metadata", metadataHeaders=["From", "Subject", "Date"]).execute()
            h = {x["name"].lower(): x["value"] for x in msg.get("payload", {}).get("headers", [])}
            try:
                when = parsedate_to_datetime(h.get("date", "")).isoformat()
            except (TypeError, ValueError):
                when = None
            out.append({"gmail_id": m["id"], "sender": h.get("from", ""), "subject": h.get("subject", ""),
                        "received_at": when, "snippet": msg.get("snippet", "")})
        token = resp.get("nextPageToken")
        if not token:
            break
    return out[:limit]


def sync(store=None, service=None, query: str | None = None) -> dict:
    store = store or get_store()
    service = service or gmail_service()
    query = query or os.getenv("GMAIL_QUERY", "label:Clients newer_than:30d")
    me = {x.strip().lower() for x in os.getenv("GMAIL_SELF", "").split(",") if x.strip()}
    counts = {"new client": 0, "logged": 0, "skipped": 0}
    db = store.all()
    for m in sorted(fetch(service, query), key=lambda m: m["received_at"] or ""):
        if parse_sender(m["sender"])[1] in me:
            counts["skipped"] += 1
            continue
        counts[record_email(store, m["sender"], m["gmail_id"], m["subject"], m["received_at"],
                            m["snippet"], db=db)] += 1
    return counts


if __name__ == "__main__":
    try:
        c = sync()
    except RuntimeError as err:
        sys.exit(f"Setup problem: {err}")
    print(f"{c['new client']} new clients, {c['logged']} emails logged, {c['skipped']} skipped.")
