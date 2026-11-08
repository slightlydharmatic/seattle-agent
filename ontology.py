"""The event ontology: every event linked to its category, venue, neighborhood, source, and month.

    build(trace)      -> {"nodes": [...], "edges": [...]}   the full graph, one node per thing
    summary(graph)    -> the question-answering tables the app shows
    profile(trace)    -> when events happen, what they are, and who hosts them (the Ontology page)

Node types:  Event, Category, Venue, Neighborhood, Source, Month, Status
Edge types:  IS_A (Event -> Category)          HAPPENS_AT (Event -> Venue)
             IN_AREA (Venue -> Neighborhood)   FOUND_ON (Event -> Source)
             IN_MONTH (Event -> Month)         HAS_STATUS (Event -> Status)
             DUPLICATE_OF (Event -> Event)
"""
from collections import Counter, defaultdict
from datetime import date
from urllib.parse import urlparse

from agents.reasoner import categorize

LIVE = {"Pick", "Publish"}


def _site(url: str, custom: bool) -> str:
    if custom:
        return "added by you"
    url = str(url or "")
    return urlparse(url).netloc.removeprefix("www.") if url.startswith("http") else (url or "unknown")


def _clean(text) -> str:
    return " ".join(str(text or "").split())


def build(trace: list[dict]) -> dict:
    nodes: dict[str, dict] = {}
    edges: Counter = Counter()

    def node(kind: str, label: str, **props) -> str:
        nid = f"{kind}:{label.lower()}"
        n = nodes.setdefault(nid, {"id": nid, "type": kind, "label": label, "events": 0, "live": 0, **props})
        return n["id"]

    for t in trace:
        status = t["status"]
        live = status in LIVE
        ev = node("Event", f"{t['title']} · {t['id']}", title=t["title"], status=status,
                  date=t["date"].isoformat() if isinstance(t.get("date"), date) else None)
        nodes[ev]["events"] = 1
        nodes[ev]["live"] = int(live)
        if status == "Filtered":
            nodes[ev]["filter_kind"] = ("paid" if t.get("filter_category") in
                                        ("Price listed", "Tickets required", "Price in description") else "topic")

        links = []
        cat = t.get("category") or categorize(t)
        links.append(("IS_A", node("Category", cat)))
        venue = _clean(t.get("venue"))
        hood = _clean(t.get("neighborhood"))
        if venue:
            v = node("Venue", venue)
            links.append(("HAPPENS_AT", v))
            if hood:
                edges[(v, node("Neighborhood", hood), "IN_AREA")] += 1
        if hood:
            links.append(("IN_AREA", node("Neighborhood", hood)))
        links.append(("FOUND_ON", node("Source", _site(t.get("source"), t.get("custom")))))
        if isinstance(t.get("date"), date):
            links.append(("IN_MONTH", node("Month", f"{t['date']:%B %Y}")))
        links.append(("HAS_STATUS", node("Status", status)))
        if t.get("merged_into"):
            links.append(("DUPLICATE_OF", f"Event:{t['merged_into']}"))  # resolved below

        for rel, target in links:
            edges[(ev, target, rel)] += 1
            if target in nodes and nodes[target]["type"] != "Event":
                nodes[target]["events"] += 1
                nodes[target]["live"] += int(live)

    # DUPLICATE_OF edges point at event ids; map them to the real event node ids.
    by_id = {n["label"].rsplit(" · ", 1)[-1]: nid for nid, n in nodes.items() if n["type"] == "Event"}
    resolved = Counter()
    for (a, b, rel), k in edges.items():
        if rel == "DUPLICATE_OF":
            b = by_id.get(b.split(":", 1)[1], b)
        resolved[(a, b, rel)] += k

    return {
        "nodes": list(nodes.values()),
        "edges": [{"source": a, "target": b, "rel": rel, "count": k} for (a, b, rel), k in resolved.items()],
    }


def summary(graph: dict) -> dict:
    """Answer the business questions from the graph."""
    nodes = {n["id"]: n for n in graph["nodes"]}
    out = defaultdict(lambda: defaultdict(list))
    for e in graph["edges"]:
        out[e["source"]][e["rel"]].append(e["target"])

    def first(eid, rel):
        t = out[eid].get(rel)
        return nodes[t[0]]["label"] if t and t[0] in nodes else None

    rows = []
    for nid, n in nodes.items():
        if n["type"] != "Event":
            continue
        rows.append({
            "event": nid, "status": n["status"], "live": bool(n["live"]),
            "category": first(nid, "IS_A"), "venue": first(nid, "HAPPENS_AT"),
            "neighborhood": first(nid, "IN_AREA"), "source": first(nid, "FOUND_ON"),
            "month": first(nid, "IN_MONTH"), "duplicate_of": first(nid, "DUPLICATE_OF"),
        })

    live = [r for r in rows if r["live"]]
    kept = [r for r in rows if r["status"] != "Duplicate"]

    # Neighborhood x category, live events only
    hood_cat = Counter((r["neighborhood"], r["category"]) for r in live if r["neighborhood"])

    # Venues with more than one free event: partnership leads
    venue_counts = Counter(r["venue"] for r in live if r["venue"])
    venue_hood = {r["venue"]: r["neighborhood"] for r in live if r["venue"]}
    repeat_venues = [(v, venue_hood.get(v) or "", k) for v, k in venue_counts.most_common() if k > 1]

    # Sources: how many events each found, how many only it found, how many were paid
    dup_targets = Counter(nodes[t]["label"] for r in rows for t in out[r["event"]].get("DUPLICATE_OF", [])
                          if t in nodes)
    sources = defaultdict(lambda: {"found": 0, "live": 0, "unique": 0, "paid": 0, "repeats": 0})
    for r in rows:
        s = sources[r["source"]]
        s["found"] += 1
        s["live"] += r["live"]
        s["paid"] += r["status"] == "Filtered" and _is_paid(nodes, r["event"])
        if r["status"] == "Duplicate":
            s["repeats"] += 1
        elif nodes[r["event"]]["label"] not in dup_targets:
            s["unique"] += 1

    # Categories: free vs paid
    cats = defaultdict(lambda: {"free": 0, "paid": 0, "held": 0})
    for r in kept:
        c = cats[r["category"]]
        if r["live"]:
            c["free"] += 1
        elif r["status"] == "Filtered" and _is_paid(nodes, r["event"]):
            c["paid"] += 1
        elif r["status"] == "Needs review":
            c["held"] += 1

    by_month = Counter((r["month"], r["category"]) for r in live if r["month"])
    return {"rows": rows, "hood_cat": hood_cat, "repeat_venues": repeat_venues,
            "sources": dict(sources), "categories": dict(cats), "by_month": by_month}


def _is_paid(nodes: dict, eid: str) -> bool:
    return nodes[eid].get("filter_kind") == "paid"


# Who puts the event on, by kind of host. Read from the venue name first, then the title.
# First match wins, so the order matters (a hotel ballroom "fair" is a hotel, not a market).
HOSTS = [
    ("Libraries", ("library",)),
    ("Hotels", ("hotel", "sheraton", "westin", "hyatt", "embassy suites", "fairmont", "w seattle", "w bellevue")),
    ("Museums & galleries", ("museum", "gallery", "galleries", "art walk", "frye", "aquarium", "conservatory",
                             "chihuly", "design center")),
    ("Parks & outdoors", ("park", "beach", "trail", "garden", "arboretum", "zoo", "preserve", "nature", "environmental",
                          "lake", "waterfront", "pier", "marina", "cruise", "golf", "fountain")),
    ("Markets & fairs", ("market", "fairground", " fair ", "bazaar", "pop-up", "convention", "farm")),
    ("Bars, cafes & restaurants", ("brew", " bar ", "taproom", "tavern", " pub", "cafe", "café", "coffee", "cellars",
                                   "winery", "wines", "restaurant", "mcmenamins", "alehouse", "lounge", "kitchen",
                                   "distillery", "oyster", "steak", "sushi", "the cove", "jazz alley")),
    ("Music & theater venues", ("theatre", "theater", " hall", "crocodile", "triple door", "cinema", "siff", "arena",
                                "dome", "stadium", "field", "performing", "performance", "auditorium", "kexp",
                                "productions", "showbox", "neptune", "neumos", "armory", "club", "arts center",
                                "center for the arts", "avenue arts", "film forum", "comedy", "pledge", "music", "dance",
                                "trapeze", "rink", "downs", "gameworks")),
    ("Schools & universities", ("university of", "college", "school", "institute")),
    ("Community & faith groups", ("church", "temple", "cathedral", "sons of norway", "cultural", "community", "nordic",
                                  "jewish", "mosque", "parish", "st. ", "saint", "shepherd", "spiritual",
                                  "phinney center", "foundation", "longhouse")),
    ("Shops & local businesses", ("shop", "store", "camera", "book", "studio", "salon", "therapy", "boutique", "chamber",
                                  "boxyard", "collective", "regus", "extraslice", "lululemon")),
    ("City & public spaces", ("seattle center", "westlake", "city of", "discover", "district", "downtown", "plaza",
                              "square", "tower", "village", "street", " way")),
]
UNSURE = "Not sure yet"
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def host_type(venue: str, title: str = "") -> str:
    """The kind of host behind an event, e.g. "Libraries" or "Bars, cafes & restaurants"."""
    for text in (venue, title):
        low = f" {_clean(text)} ".lower()
        for name, words in HOSTS:
            if any(w in low for w in words):
                return name
    return UNSURE


def profile(trace: list[dict], live_only: bool = True) -> dict:
    """When events happen, what they are, and who hosts them. Repeats are counted once."""
    rows = [t for t in trace if t.get("status") != "Duplicate" and (not live_only or t.get("status") in LIVE)]
    days, kinds, hosts, day_kind = Counter(), Counter(), Counter(), Counter()
    for t in rows:
        kind = t.get("category") or categorize(t)
        kinds[kind] += 1
        hosts[host_type(t.get("venue"), t.get("title"))] += 1
        if isinstance(t.get("date"), date):
            day = DAYS[t["date"].weekday()]
            days[day] += 1
            day_kind[(kind, day)] += 1
    return {"n": len(rows), "days": {d: days[d] for d in DAYS}, "kinds": kinds, "hosts": hosts,
            "day_kind": day_kind}
