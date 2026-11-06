"""Circuit breaker: a bad run never replaces a good list.

Before a new fetch becomes snapshots/latest.json (what readers see), it's compared
with the last published one. If it looks broken, it's saved to snapshots/held.json
instead, the public list stays as it was, and the team decides: publish anyway or discard.

Trips when (any one):
  - the run found less than half as many events as last time
  - more than half of the listing pages failed to load
  - more than half of last run's productive sources went silent
  - the AI filtered out more than 60% of the events it scored

Warns (doesn't trip) when a single source that usually has events returns none.
"""
import json
from collections import Counter
from datetime import datetime, timezone
from urllib.parse import urlparse

from config import PROJECT_DIR

HELD = PROJECT_DIR / "snapshots" / "held.json"

MIN_EVENT_RATIO = 0.5      # new events / last run's events
MAX_PAGE_FAIL = 0.5        # failed pages / pages tried
MAX_SILENT_SOURCES = 0.5   # productive sources gone quiet / productive sources
MAX_AI_FILTERED = 0.6      # AI low relevance / events the AI scored
MIN_BASELINE = 10          # below this many events last time, ratios are too noisy to judge


def site(url: str) -> str:
    host = urlparse(url or "").netloc.lower()
    return host[4:] if host.startswith("www.") else host


def by_source(events: list[dict]) -> Counter:
    return Counter(site(e.get("source", "")) for e in events or [])


def check(new: dict, old: dict | None, curated: dict | None = None) -> dict:
    """Compare a new fetch with the last published snapshot. Returns {tripped, reasons, warnings, metrics}."""
    reasons, warnings = [], []
    n_new = len(new.get("events_raw") or [])
    n_old = len((old or {}).get("events_raw") or [])
    tried = len(new.get("source_urls") or [])
    failed = len(new.get("pages_failed") or [])
    metrics = {"events": n_new, "events_last": n_old, "pages": tried, "pages_failed": failed}

    if n_new == 0:
        reasons.append("The run found no events at all.")
    elif n_old >= MIN_BASELINE and n_new < MIN_EVENT_RATIO * n_old:
        reasons.append(f"Found {n_new} events, less than half of last run's {n_old}.")

    if tried and failed / tried > MAX_PAGE_FAIL:
        reasons.append(f"{failed} of {tried} listing pages failed to load.")

    old_src, new_src = by_source((old or {}).get("events_raw")), by_source(new.get("events_raw"))
    productive = [s for s, k in old_src.items() if k >= 3 and s]
    silent = [s for s in productive if new_src.get(s, 0) == 0]
    metrics["sources"] = dict(new_src)
    if productive and len(silent) / len(productive) > MAX_SILENT_SOURCES:
        reasons.append(f"{len(silent)} of {len(productive)} usual sources returned nothing: {', '.join(sorted(silent))}.")
    elif silent:
        warnings.append(f"Returned nothing this time: {', '.join(sorted(silent))}.")

    if curated:
        ai_low = sum(1 for e in curated.get("events_filtered", []) if e.get("filter_category") == "AI: low relevance")
        unsure = sum(1 for e in curated.get("events_review", [])
                     if any(str(r).startswith("AI unsure") for r in e.get("review_reasons", [])))
        kept = sum(1 for e in curated.get("events_valid", []) if e.get("ai"))
        scored = ai_low + unsure + kept
        metrics["ai_filtered_share"] = round(ai_low / scored, 2) if scored else None
        if scored >= MIN_BASELINE and ai_low / scored > MAX_AI_FILTERED:
            reasons.append(f"The AI filtered out {ai_low} of {scored} events ({ai_low / scored:.0%}). "
                           "That usually means the instructions or the sources changed.")

    return {"tripped": bool(reasons), "reasons": reasons, "warnings": warnings, "metrics": metrics,
            "checked_at": datetime.now(timezone.utc).isoformat(timespec="minutes")}


def hold(snap: dict, result: dict) -> None:
    HELD.parent.mkdir(parents=True, exist_ok=True)
    HELD.write_text(json.dumps({"snapshot": snap, "breaker": result}, indent=1, default=str))


def held() -> dict | None:
    try:
        return json.loads(HELD.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def clear() -> None:
    HELD.unlink(missing_ok=True)
