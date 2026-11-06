"""Fetch listing pages, curate the events with the AI classifier, and save the snapshot.

    python refresh.py

Run weekly by .github/workflows/refresh.yml. Needs OPENAI_API_KEY and TAVILY_API_KEY.
The classifier only sees events it hasn't scored before, and uses the team's
latest thumbs up / down as examples.
"""
import calendar
import logging
import sys
from datetime import date

import breaker
import filters
import snapshot
from pipeline import build_graph


HELD_EXIT = 3  # tells the weekly job the run was held, so GitHub emails you


def three_months_out(today: date) -> date:
    y, m = divmod(today.month - 1 + 2, 12)
    y, m = today.year + y, m + 1
    return date(y, m, calendar.monthrange(y, m)[1])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        raw = build_graph(stop_after="extractor").invoke({"query": "free events in Seattle", "max_pages": 20})
        old = snapshot.load() or {}
        if not raw.get("events_raw"):
            result = breaker.check(raw, old)
            breaker.hold(snapshot.build(raw), result)
            print("Circuit breaker: no events came back, so the public list was NOT changed.")
            sys.exit(HELD_EXIT)
        rules = filters.load()
        curated = build_graph(skip_until="normalizer", stop_after="curator").invoke({
            **raw, "curation": old.get("curation") or {}, "curate_live": True,
            "window_end": three_months_out(date.today()), "filters": rules,
            **rules.get("curation", {}),
        })
    except RuntimeError as err:
        sys.exit(f"Setup problem: {err}")
    snap = snapshot.build({**raw, "curation": curated["curation"]})
    result = breaker.check(raw, old, curated)
    for w in result["warnings"]:
        print("Warning:", w)
    if result["tripped"]:
        breaker.hold(snap, result)
        print("Circuit breaker held this run. The public list was NOT changed.")
        for r in result["reasons"]:
            print(" -", r)
        print("Open the app (signed in) to publish anyway or discard.")
        sys.exit(HELD_EXIT)
    breaker.clear()
    snapshot.write(snap)
    print(f"Saved {len(snap['events_raw'])} events from {len(snap['pages'] or [])} pages; "
          f"{len(snap['curation'])} events have AI scores.")
