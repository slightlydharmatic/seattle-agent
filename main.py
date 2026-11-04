"""Run the pipeline from the command line.

    python main.py                       # this week's free Seattle events
    python main.py --days 7 --picks 5    # one week out, five suggested picks
    python main.py --include-paid        # keep paid events too
"""
import argparse
import logging

from config import OUTPUT_DIR
from pipeline import build_graph


def main() -> None:
    p = argparse.ArgumentParser(description="Find events for Seattle Unlocked.")
    p.add_argument("--query", default="free events in Seattle this week")
    p.add_argument("--days", type=int, default=14, help="how far ahead to look")
    p.add_argument("--pages", type=int, default=10, help="max listing pages to read")
    p.add_argument("--picks", type=int, default=6, help="how many picks to suggest")
    p.add_argument("--include-paid", action="store_true")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args()

    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING,
                        format="%(levelname)s %(message)s")

    try:
        result = build_graph().invoke({
            "query": args.query,
            "window_days": args.days,
            "max_pages": args.pages,
            "max_picks": args.picks,
            "free_only": not args.include_paid,
            "output_dir": OUTPUT_DIR,
        })
    except RuntimeError as err:  # setup problems: show the fix, not a stack trace
        raise SystemExit(f"Setup problem: {err}")
    print(result["report"])
    if result.get("csv_path"):
        print(f"\nSheet rows saved to {result['csv_path']}")


if __name__ == "__main__":
    main()
