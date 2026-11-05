"""Step 4: decide which events are ready to publish.

Every event either passes all checks or goes to human review with a reason.
Nothing is silently dropped. Each event keeps its full checklist so the UI
can show exactly what passed and what failed.
"""
import re
from datetime import date, timedelta

from config import BLOCKED_TOPICS

_BLOCKED = {topic: re.compile(r"\b(?:" + "|".join(pats) + r")\b", re.I)
            for topic, pats in BLOCKED_TOPICS.items()}


# Signs an event costs money even when the cost field says nothing.
_PAID = re.compile(
    r"buy (?:your )?tickets?|get (?:your )?tickets?|tickets? (?:on sale|available|required|from|start)"
    r"|purchase tickets?|\$\s?\d|admission:? \$|cover charge|presale|ticketmaster|\baxs\b|etix"
    r"|seetickets|dice\.fm|\bsold out\b",
    re.I,
)


def paid_reason(e: dict) -> str | None:
    """Return why an event isn't free (e.g. 'not free ($45)', 'tickets required'), or None."""
    cost = str(e.get("cost") or "")
    if cost and cost not in ("Free", "Not listed"):
        return f"not free ({cost})"
    if str(e.get("ticketed")).lower() == "true":
        return "tickets required"
    text = " ".join(str(e.get(k) or "") for k in ("title", "description"))
    m = _PAID.search(text)
    if m:
        return f"tickets required ({m.group(0).lower()})"
    return None


def blocked_topic(e: dict) -> str | None:
    """Return why an event is off-topic (e.g. 'real estate: escrow'), or None."""
    text = " ".join(str(e.get(k) or "") for k in ("title", "description", "venue"))
    for topic, rx in _BLOCKED.items():
        m = rx.search(text)
        if m:
            return f"{topic} ({m.group(0).lower()})"
    return None


def checklist(e: dict, today: date, last_day: date, free_only: bool) -> list[dict]:
    """Run every check and return [{"check": ..., "passed": bool, "detail": ...}].

    Check names are short on purpose: the app shows them as chips (Title, Date, Venue, Free).
    """
    d = e.get("date")
    if d is None:
        date_ok, date_detail = False, "date not understood"
    elif d < today:
        date_ok, date_detail = False, "already happened"
    elif d > last_day:
        date_ok, date_detail = False, f"after {last_day:%b} {last_day.day}"
    else:
        date_ok, date_detail = True, f"{d:%a %b} {d.day}"

    checks = [
        {"check": "Title", "passed": bool(e.get("title")), "detail": "missing title"},
        {"check": "Date", "passed": date_ok, "detail": date_detail},
        {"check": "Venue", "passed": bool(e.get("venue")), "detail": "missing venue"},
    ]
    if free_only and not e.get("custom"):  # events you add can be paid, e.g. sponsors
        # Paid events never get this far (they're filtered out); this catches unknown cost.
        free = e.get("cost") == "Free"
        checks.append({"check": "Free", "passed": free, "detail": "cost not listed"})
    for c in checks:
        if c["passed"] and c["check"] != "Date":
            c["detail"] = "ok"
    return checks


def last_day(state: dict, today: date) -> date:
    """End of the run's range: an explicit window_end, else today plus window_days."""
    return state.get("window_end") or today + timedelta(days=state.get("window_days", 14))


def check(e: dict, today: date, end: date, free_only: bool) -> list[str]:
    """Return the reasons an event needs review. An empty list means it passes."""
    return [c["detail"] for c in checklist(e, today, end, free_only) if not c["passed"]]


def validate(state: dict) -> dict:
    today = state.get("today") or date.today()
    end = last_day(state, today)
    free_only = state.get("free_only", True)

    valid, review, filtered = [], [], []
    for e in state.get("events_clean", []):
        topic = None if e.get("custom") else blocked_topic(e)  # your own events are never filtered
        if not topic and free_only and not e.get("custom"):
            topic = paid_reason(e)
        if topic:
            filtered.append({**e, "filter_reason": topic})
            continue
        e["checks"] = checklist(e, today, end, free_only)
        reasons = [c["detail"] for c in e["checks"] if not c["passed"]]
        if reasons:
            review.append({**e, "review_reasons": reasons})
        else:
            valid.append(e)

    state["events_valid"] = valid
    state["events_review"] = review
    state["events_filtered"] = filtered
    return state
