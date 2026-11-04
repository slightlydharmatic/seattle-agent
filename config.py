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
    "https://www.events12.com/seattle/",
    "https://www.eventbrite.com/d/wa--seattle/free--events/",
    "https://everout.com/seattle/events/?category=community",
    "https://do206.com/free-events-seattle",
]

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
