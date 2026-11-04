"""Step 5: tag each event with a category and suggest picks.

Picks are suggestions only. The "pick" column stays for a person to confirm
in the sheet, and the website features whatever is marked there. Each event
records why it scored what it did and why it was or wasn't picked.
"""
from collections import Counter

CATEGORIES = {
    "Music": ["music", "concert", "band", "dj", "jazz", "live show", "orchestra", "choir"],
    "Art": ["art", "gallery", "exhibit", "museum", "painting", "artwalk", "art walk"],
    "Festival": ["festival", "fair", "celebration", "parade", "fest"],
    "Market": ["market", "vendors", "flea", "vintage", "makers"],
    "Comedy": ["comedy", "stand-up", "standup", "improv", "open mic"],
    "Outdoors": ["hike", "park", "trail", "garden", "kayak", "beach", "cleanup"],
    "Food & Drink": ["food", "dinner", "brunch", "tasting", "brew", "wine", "coffee", "happy hour"],
    "Sports": ["game", "run", "5k", "soccer", "pickleball", "match", "race"],
    "Wellness": ["yoga", "meditation", "fitness", "wellness"],
    "Film": ["film", "movie", "screening", "cinema"],
}


def categorize(e: dict) -> str:
    text = f"{e.get('title', '')} {e.get('description', '')}".lower()
    for cat, words in CATEGORIES.items():
        if any(w in text for w in words):
            return cat
    return "Community"


def score_breakdown(e: dict) -> list[tuple[str, int]]:
    """Points an event earns toward being featured, with the reason for each."""
    parts = []
    if e.get("time"):
        parts.append(("Start time listed", 1))
    if e.get("neighborhood"):
        parts.append(("Neighborhood listed", 1))
    if e.get("description"):
        parts.append(("Has a description", 1))
    if e.get("date") and e["date"].weekday() >= 4:
        parts.append(("Friday to Sunday", 2))
    if e.get("link") and e.get("link") != e.get("source"):
        parts.append(("Has its own event link", 1))
    return parts


def score(e: dict) -> int:
    return sum(p for _, p in score_breakdown(e))


def _choose_picks(events: list[dict], max_picks: int) -> None:
    per_cat, picks = Counter(), 0
    # Events you added and marked "feature" are always picks, and count toward the limit.
    for e in events:
        if e.get("feature"):
            e["pick_suggested"], e["pick_reason"] = True, "added by you as a pick"
            per_cat[e["category"]] += 1
            picks += 1
    for e in sorted(events, key=lambda e: (-e["score"], e["date"])):
        if e.get("feature"):
            continue
        if picks >= max_picks:
            e["pick_suggested"], e["pick_reason"] = False, f"month already has {max_picks} picks"
        elif per_cat[e["category"]] >= 2:
            e["pick_suggested"], e["pick_reason"] = False, f"already 2 {e['category']} picks this month"
        else:
            e["pick_suggested"], e["pick_reason"] = True, f"score {e['score']}, top in {e['category']}"
            per_cat[e["category"]] += 1
            picks += 1


def reason(state: dict) -> dict:
    events = state.get("events_valid", [])
    max_picks = state.get("max_picks", 6)
    for e in events:
        e["category"] = e.get("category") or categorize(e)
        e["score_parts"] = score_breakdown(e)
        e["score"] = sum(p for _, p in e["score_parts"])

    # Highest scores first, at most two per category so the feature stays varied.
    # Picks are chosen month by month, since the sheet has one tab per month.
    by_month: dict[tuple, list] = {}
    for e in events:
        by_month.setdefault((e["date"].year, e["date"].month), []).append(e)
    for month_events in by_month.values():
        _choose_picks(month_events, max_picks)

    state["events_valid"] = events
    return state
