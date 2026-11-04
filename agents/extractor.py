"""Step 2: read each listing page and pull out individual events.

A listing page holds many events, so we hand its text to a model and ask for
a structured list back, one entry per event.
"""
import json
import logging
from datetime import date

from agents import clients
from config import OPENAI_MODEL

log = logging.getLogger(__name__)

MAX_PAGE_CHARS = 24_000

PROMPT = """You read Seattle event listing pages and return the events on them.
Today is {today}. Return JSON: {{"events": [ ... ]}}. Each event has:
  title        the event name
  date         YYYY-MM-DD (resolve words like "Saturday" using today's date)
  time         start time like "7pm", or "" if not listed
  venue        where it happens
  neighborhood Seattle neighborhood or nearby city, or ""
  cost         "Free" or the price as written
  description  one sentence, in plain words
  link         the event's own URL if the page shows one, else ""
Only include real events in the Seattle area. Do not invent details.
If the page has no events, return {{"events": []}}."""


def parse_events(raw_json: str, source_url: str) -> list[dict]:
    """Turn the model's JSON reply into event dicts. Bad replies give []."""
    try:
        data = json.loads(raw_json)
    except (json.JSONDecodeError, TypeError):
        log.warning("Extractor: could not read model reply for %s", source_url)
        return []
    events = data.get("events", []) if isinstance(data, dict) else []
    out = []
    for e in events:
        if not isinstance(e, dict):
            continue
        e = {k: (str(v).strip() if v is not None else "") for k, v in e.items()}
        e["source"] = source_url
        e["link"] = e.get("link") or source_url
        out.append(e)
    return out


def _events_from_page(url: str, content: str, today: date) -> list[dict]:
    reply = clients.openai().chat.completions.create(
        model=OPENAI_MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": PROMPT.format(today=today.isoformat())},
            {"role": "user", "content": f"URL: {url}\n\n{content[:MAX_PAGE_CHARS]}"},
        ],
    )
    return parse_events(reply.choices[0].message.content, url)


def extract(state: dict) -> dict:
    urls = state.get("source_urls", [])
    today = state.get("today") or date.today()
    events, failed, page_log = [], [], []

    if urls:
        try:
            pages = clients.tavily().extract(urls=urls, extract_depth="advanced")
        except RuntimeError:
            raise  # missing key: stop with the setup message
        except Exception as err:
            log.warning("Extractor: could not read pages: %s", err)
            pages = {"results": [], "failed_results": [{"url": u} for u in urls]}
        failed = [f.get("url") for f in pages.get("failed_results", [])]
        for page in pages.get("results", []):
            url, content = page.get("url", ""), page.get("raw_content") or ""
            if not content.strip():
                failed.append(url)
                page_log.append({"url": url, "status": "empty page", "events": 0})
                continue
            try:
                found = _events_from_page(url, content, today)
            except RuntimeError:
                raise  # setup problem (missing package or key): stop with the fix
            except Exception as err:
                if getattr(err, "code", None) == "insufficient_quota" or "no credits" in str(err).lower():
                    raise RuntimeError(
                        "Your OpenAI account has no credits. Add some at "
                        "platform.openai.com/settings/organization/billing, then run again."
                    ) from None
                if getattr(err, "status_code", None) in (401, 403):
                    raise RuntimeError(
                        "OpenAI rejected the API key in .env. Create a new key at "
                        "platform.openai.com/api-keys and replace OPENAI_API_KEY in .env."
                    ) from None
                log.warning("Extractor: model call failed for %s: %s", url, err)
                failed.append(url)
                page_log.append({"url": url, "status": "model error", "events": 0})
                continue
            log.info("Extractor: %d events from %s", len(found), url)
            page_log.append({"url": url, "status": "read", "events": len(found)})
            events += found

    logged = {p["url"] for p in page_log}
    page_log += [{"url": u, "status": "could not load", "events": 0} for u in failed if u not in logged]
    for i, e in enumerate(events, 1):
        e["id"] = f"e{i:03d}"
    state["events_raw"] = events
    state["pages_failed"] = failed
    state["pages"] = page_log
    return state
