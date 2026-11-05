"""Filter rules the team can edit. Saved to data/filters.json."""
import copy
import json
import re
from functools import lru_cache

from config import DEFAULT_FILTERS, PROJECT_DIR

PATH = PROJECT_DIR / "data" / "filters.json"

# Reason categories, in the order the app shows them.
PRICE, TICKETS, PRICE_TEXT = "Price listed", "Tickets required", "Price in description"


def load() -> dict:
    rules = copy.deepcopy(DEFAULT_FILTERS)
    try:
        saved = json.loads(PATH.read_text())
        rules.update({k: v for k, v in saved.items() if k in rules})
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return rules


def save(rules: dict) -> None:
    PATH.parent.mkdir(parents=True, exist_ok=True)
    PATH.write_text(json.dumps(rules, indent=2))


def reset() -> dict:
    save(copy.deepcopy(DEFAULT_FILTERS))
    return load()


def event_key(e: dict) -> str:
    """Stable across runs (ids are not): simplified title plus date."""
    d = e.get("date")
    title = re.sub(r"[^a-z0-9]", "", str(e.get("title") or "").lower())
    return f"{title}|{d.isoformat() if hasattr(d, 'isoformat') else d or ''}"


@lru_cache(maxsize=64)
def _phrase_rx(terms: tuple) -> re.Pattern | None:
    parts = []
    for t in terms:
        t = t.strip().lower()
        if not t:
            continue
        body = r"[\s-]+".join(re.escape(w) for w in re.split(r"[\s-]+", t))
        parts.append(body + "s?")
    if not parts:
        return None
    return re.compile(r"(?<![\w])(?:" + "|".join(parts) + r")(?![\w])", re.I)


def match(terms: list[str], text: str) -> str | None:
    rx = _phrase_rx(tuple(terms))
    m = rx.search(text) if rx else None
    return m.group(0).lower() if m else None


_DOLLAR = re.compile(r"\$\s?\d")


def reason(e: dict, rules: dict, free_only: bool) -> tuple[str, str] | None:
    """Return (category, detail) if an event should be filtered out, else None."""
    if e.get("custom") or event_key(e) in set(rules.get("allow", [])):
        return None
    text = " ".join(str(e.get(k) or "") for k in ("title", "description", "venue"))
    for topic, terms in rules.get("topics", {}).items():
        hit = match(terms, text)
        if hit:
            return topic, hit
    if not free_only:
        return None
    cost = str(e.get("cost") or "")
    if rules.get("price_listed", True) and cost and cost not in ("Free", "Not listed"):
        return PRICE, cost
    if rules.get("tickets", True):
        if str(e.get("ticketed")).lower() == "true":
            return TICKETS, "marked ticketed by the extractor"
        hit = match(rules.get("ticket_terms", []), " ".join(str(e.get(k) or "") for k in ("title", "description")))
        if hit:
            return TICKETS, hit
    if rules.get("price_in_text", True):
        m = _DOLLAR.search(" ".join(str(e.get(k) or "") for k in ("title", "description")))
        if m:
            return PRICE_TEXT, m.group(0)
    return None
