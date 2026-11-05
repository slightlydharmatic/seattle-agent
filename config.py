"""Settings for the Seattle Unlocked event agent.

Loads .env from the project folder once. Never prints or logs secret values.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parent
load_dotenv(PROJECT_DIR / ".env")

# Listing pages we trust. The retriever always reads these, then adds any
# matching pages a search turns up on the same sites.
SOURCE_PAGES = [
    "https://www.greaterseattleonthecheap.com/this-week/",
    "https://www.seattlecenter.com/events/event-calendar",
    "https://www.eventbrite.com/d/wa--seattle/free--events/",
    "https://everout.com/seattle/events/?category=community",
    "https://do206.com/free-events-seattle",
]

# Sites that publish one page per month. The retriever adds this month and the
# next two, so the run sees what's coming, not a cached copy of last month.
MONTHLY_PAGES = [
    "https://www.events12.com/seattle/{month}/",
]


def month_pages(today, months_ahead: int = 3) -> list[str]:
    import calendar
    names = []
    for i in range(months_ahead):
        m = (today.month - 1 + i) % 12 + 1
        names.append(calendar.month_name[m].lower())
    return [tpl.format(month=n) for tpl in MONTHLY_PAGES for n in names]


OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OUTPUT_DIR = PROJECT_DIR / "output"


def require(name: str) -> str:
    """Return an environment variable, or fail with a clear fix."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"{name} is not set. Copy .env.example to .env and add your key."
        )
    return value


# Topics Seattle Unlocked never features. An event whose title, description, or
# venue matches any of these is filtered out (still listed in the full record).
BLOCKED_TOPICS = {
    "real estate": [
        r"real[\s-]?estate", r"realtors?", r"realty", r"brokerage", r"escrow",
        r"mortgage", r"refinanc\w*", r"home ?equity", r"home ?buy(?:er|ers|ing)",
        r"first[\s-]time (?:home ?)?buyers?", r"home ?sell(?:er|ers|ing)", r"open house",
        r"property invest\w*", r"investment propert\w*", r"rental propert\w*", r"landlords?",
        r"house hunting", r"condo tour", r"title company", r"d?adus?", r"accessory dwelling",
        r"zillow", r"redfin", r"windermere", r"coldwell", r"keller williams", r"re/max",
    ],
}
