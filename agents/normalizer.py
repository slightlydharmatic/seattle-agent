"""Step 3: clean up fields and remove duplicates.

The same event often shows up on several listing sites, so we match on a
simplified title plus the date. Merged copies are recorded, not thrown away,
so the UI can show what was combined.
"""
import re
from datetime import date, datetime

DATE_FORMATS = ["%Y-%m-%d", "%B %d, %Y", "%b %d, %Y", "%m/%d/%Y", "%A, %B %d, %Y"]
FREE_WORDS = {"free", "$0", "0", "no cover", "free admission", "free entry", "free to attend",
              "free event", "free, rsvp", "free with rsvp", "free (rsvp)", "free with registration"}
UNKNOWN = "Not listed"


def parse_date(value) -> date | None:
    if isinstance(value, date):
        return value
    text = str(value or "").strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def title_key(title: str) -> str:
    return re.sub(r"[^a-z0-9]", "", title.lower())


def clean_cost(cost: str) -> str:
    text = (cost or "").strip()
    if not text:
        return UNKNOWN  # never assume free
    return "Free" if text.lower() in FREE_WORDS else text


def _richness(e: dict) -> int:
    return sum(bool(e.get(k)) for k in ("time", "venue", "neighborhood", "description"))


def normalize(state: dict) -> dict:
    best: dict[tuple, dict] = {}
    duplicates: list[dict] = []
    custom = [{**e, "id": e.get("custom_id") or f"c{i:03d}", "custom": True, "source": "Added by you"}
              for i, e in enumerate(state.get("custom_events", []), 1)]
    for i, e in enumerate(state.get("events_raw", []) + custom, 1):
        e = dict(e)
        e.setdefault("id", f"e{i:03d}")
        e["date_as_listed"] = str(e.get("date", ""))
        e["title"] = re.sub(r"\s+", " ", e.get("title", "")).strip()
        e["date"] = parse_date(e.get("date"))
        e["cost"] = clean_cost(e.get("cost", ""))
        key = (title_key(e["title"]), e["date"])
        if key not in best:
            best[key] = e
            continue
        # Keep whichever copy has the most detail; record the other as merged.
        # An event you added yourself always wins over a scraped copy.
        if e.get("custom") != best[key].get("custom"):
            kept, dropped = (e, best[key]) if e.get("custom") else (best[key], e)
        else:
            kept, dropped = (e, best[key]) if _richness(e) > _richness(best[key]) else (best[key], e)
        best[key] = kept
        duplicates.append({**dropped, "merged_into": kept["id"]})

    # A copy that was kept earlier and later replaced must point at the final winner.
    final_ids = {e["id"] for e in best.values()}
    winner_by_key = {k: v["id"] for k, v in best.items()}
    for d in duplicates:
        if d["merged_into"] not in final_ids:
            d["merged_into"] = winner_by_key[(title_key(d["title"]), d["date"])]

    clean = sorted(best.values(), key=lambda e: (e["date"] or date.max, e["title"]))
    state["events_clean"] = clean
    state["duplicates"] = duplicates
    state["duplicates_removed"] = len(duplicates)
    state["events_pulled"] = len(state.get("events_raw", [])) + len(custom)
    return state
