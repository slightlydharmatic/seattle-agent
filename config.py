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


# Default filter rules. The team can change these in the app (Filters page);
# changes are saved to data/filters.json and override these defaults.
# Terms are plain words or phrases, matched as whole words, ignoring case.
DEFAULT_FILTERS = {
    "price_listed": True,        # a price in the cost field ("$15", "Varies")
    "tickets": True,             # ticket language, or the extractor marked it ticketed
    "price_in_text": True,       # a dollar amount anywhere in the title or description
    "ticket_terms": [
        "buy tickets", "get tickets", "get your tickets", "tickets on sale", "tickets available",
        "tickets required", "tickets from", "tickets start", "purchase tickets", "cover charge",
        "presale", "sold out", "ticketmaster", "axs", "etix", "seetickets", "dice.fm",
    ],
    "topics": {
        "Real estate": [
            "real estate", "realtor", "realtors", "realty", "brokerage", "escrow", "mortgage",
            "refinance", "refinancing", "home equity", "homebuyer", "homebuyers", "home buyer",
            "home buying", "first-time buyer", "first-time homebuyer", "home seller", "home selling",
            "open house", "property investing", "investment property", "rental property", "landlord",
            "landlords", "house hunting", "condo tour", "title company", "adu", "dadu",
            "accessory dwelling", "zillow", "redfin", "windermere", "coldwell banker",
            "keller williams", "re/max",
        ],
    },
    "allow": [],                 # events kept on the list even though a filter matched
}
