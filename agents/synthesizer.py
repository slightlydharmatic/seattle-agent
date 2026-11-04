"""Step 6: write the results.

Produces:
  rows    sheet rows in the Seattle Unlocked sheet's columns
          (title, date, time, spot, hood, cat, desc, cost, link, pick)
  trace   one entry for every event pulled, with its final status and why,
          so the UI can show what was pulled, chosen, merged, or held back
  report  a short text summary
"""
import csv
from datetime import date
from itertools import groupby
from pathlib import Path

SHEET_COLUMNS = ["title", "date", "time", "spot", "hood", "cat", "desc", "cost", "link", "pick"]

# Statuses, in the order the UI shows them.
PICK, PUBLISH, REVIEW, MERGED = "Pick", "Publish", "Needs review", "Duplicate"
STATUSES = [PICK, PUBLISH, REVIEW, MERGED]


def to_row(e: dict) -> dict:
    d = e.get("date")
    return {
        "title": e.get("title", ""),
        "date": f"{d.strftime('%B')} {d.day}" if d else "",  # sheet style, e.g. "November 7"
        "time": e.get("time", ""),
        "spot": e.get("venue", ""),
        "hood": e.get("neighborhood", ""),
        "cat": e.get("category", ""),
        "desc": e.get("description", ""),
        "cost": e.get("cost", "Free"),
        "link": e.get("link", ""),
        "pick": "TRUE" if e.get("pick_suggested") else "FALSE",
    }


def _trace_entry(e: dict, status: str, why: str) -> dict:
    return {
        "id": e.get("id", ""),
        "status": status,
        "why": why,
        "title": e.get("title", ""),
        "date": e.get("date"),
        "date_as_listed": e.get("date_as_listed", ""),
        "time": e.get("time", ""),
        "venue": e.get("venue", ""),
        "neighborhood": e.get("neighborhood", ""),
        "category": e.get("category", ""),
        "cost": e.get("cost", ""),
        "score": e.get("score"),
        "score_parts": e.get("score_parts", []),
        "checks": e.get("checks", []),
        "description": e.get("description", ""),
        "source": e.get("source", ""),
        "link": e.get("link", ""),
        "merged_into": e.get("merged_into", ""),
        "custom": bool(e.get("custom")),
        "custom_id": e.get("custom_id", ""),
    }


def build_trace(state: dict) -> list[dict]:
    trace = []
    for e in state.get("events_valid", []):
        status = PICK if e.get("pick_suggested") else PUBLISH
        trace.append(_trace_entry(e, status, e.get("pick_reason", "")))
    for e in state.get("events_review", []):
        trace.append(_trace_entry(e, REVIEW, ", ".join(e["review_reasons"])))
    titles = {t["id"]: t["title"] for t in trace}
    for e in state.get("duplicates", []):
        trace.append(_trace_entry(e, MERGED, f"same as {titles.get(e['merged_into'], e['merged_into'])}"))
    order = {s: i for i, s in enumerate(STATUSES)}
    trace.sort(key=lambda t: (order[t["status"]], t["date"] or date.max, t["title"]))
    return trace


def build_report(state: dict) -> str:
    valid, review = state.get("events_valid", []), state.get("events_review", [])
    total = len(valid) + len(review)
    share = f"{len(review) / total:.0%}" if total else "0%"
    lines = [
        f"Pages read: {len(state.get('source_urls', []))}"
        f" ({len(state.get('pages_failed', []))} failed)",
        f"Events found: {state.get('events_pulled', len(state.get('events_raw', [])))}"
        f", duplicates removed: {state.get('duplicates_removed', 0)}",
        f"Ready to publish: {len(valid)}",
        f"Needs review: {len(review)} ({share})",
        "",
    ]
    for d, group in groupby(valid, key=lambda e: e["date"]):
        lines.append(f"=== {d:%A, %B} {d.day} ===")
        for e in group:
            star = "* " if e.get("pick_suggested") else "  "
            when = f", {e['time']}" if e.get("time") else ""
            lines.append(f"{star}{e['title']} ({e['category']}) at {e['venue']}{when}")
        lines.append("")
    if review:
        lines.append("=== Needs review ===")
        for e in review:
            lines.append(f"  {e.get('title') or '(no title)'}: {', '.join(e['review_reasons'])}")
    lines.append("")
    lines.append("* = suggested pick")
    return "\n".join(lines)


def synthesize(state: dict) -> dict:
    rows = [to_row(e) for e in state.get("events_valid", [])]
    state["rows"] = rows
    state["trace"] = build_trace(state)
    state["report"] = build_report(state)

    out_dir = state.get("output_dir")
    if out_dir:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        stamp = (state.get("today") or date.today()).isoformat()
        path = out_dir / f"events_{stamp}.csv"
        with path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=SHEET_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
        state["csv_path"] = str(path)
    return state
