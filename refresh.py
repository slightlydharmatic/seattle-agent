"""Fetch listing pages (steps 1 and 2) and save them as the latest snapshot.

    python refresh.py

Run weekly by .github/workflows/refresh.yml. Needs OPENAI_API_KEY and TAVILY_API_KEY.
"""
import logging
import sys

import snapshot
from pipeline import build_graph

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        raw = build_graph(stop_after="extractor").invoke({"query": "free events in Seattle", "max_pages": 20})
    except RuntimeError as err:
        sys.exit(f"Setup problem: {err}")
    if not raw.get("events_raw"):
        sys.exit("No events came back, so the existing snapshot was kept.")
    snap = snapshot.save(raw)
    print(f"Saved {len(snap['events_raw'])} events from {len(snap['pages'] or [])} pages.")
