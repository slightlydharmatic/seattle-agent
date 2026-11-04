"""Step 4: decide which events are ready to publish.

Every event either passes all checks or goes to human review with a reason.
Nothing is silently dropped. Each event keeps its full checklist so the UI
can show exactly what passed and what failed.
"""
from datetime import date, timedelta


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
        free = e.get("cost") == "Free"
        checks.append({"check": "Free", "passed": free, "detail": f"not free ({e.get('cost')})"})
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

    valid, review = [], []
    for e in state.get("events_clean", []):
        e["checks"] = checklist(e, today, end, free_only)
        reasons = [c["detail"] for c in e["checks"] if not c["passed"]]
        if reasons:
            review.append({**e, "review_reasons": reasons})
        else:
            valid.append(e)

    state["events_valid"] = valid
    state["events_review"] = review
    return state
