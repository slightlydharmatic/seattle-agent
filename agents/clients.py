"""API clients, created on first use so importing the agents never needs keys."""
from functools import lru_cache

from config import require


def _missing(pkg: str) -> RuntimeError:
    return RuntimeError(f"The '{pkg}' package isn't installed. Run: pip install -r requirements.txt")


@lru_cache(maxsize=1)
def tavily():
    try:
        from tavily import TavilyClient
    except ImportError:
        raise _missing("tavily-python") from None

    return TavilyClient(api_key=require("TAVILY_API_KEY"))


@lru_cache(maxsize=1)
def openai():
    try:
        from openai import OpenAI
    except ImportError:
        raise _missing("openai") from None

    return OpenAI(api_key=require("OPENAI_API_KEY"))
