"""Step 1: decide which listing pages to read."""
import logging
from urllib.parse import urlparse

from agents import clients
from config import SOURCE_PAGES

log = logging.getLogger(__name__)


def _domain(url: str) -> str:
    return urlparse(url).netloc.removeprefix("www.")


def retrieve(state: dict) -> dict:
    query = state.get("query", "free events in Seattle this week")
    max_pages = state.get("max_pages", 10)

    urls = list(SOURCE_PAGES)
    try:
        results = clients.tavily().search(
            query=query,
            include_domains=sorted({_domain(u) for u in SOURCE_PAGES}),
            max_results=10,
        )
        urls += [r["url"] for r in results.get("results", []) if r.get("url")]
    except Exception as err:  # search is a bonus; the trusted pages still run
        log.warning("Search failed, using trusted pages only: %s", err)

    state["source_urls"] = list(dict.fromkeys(urls))[:max_pages]
    log.info("Retriever: %d pages to read", len(state["source_urls"]))
    return state
