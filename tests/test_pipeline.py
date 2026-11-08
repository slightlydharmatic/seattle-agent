"""Offline tests: no API keys or network needed. Run with `python -m pytest`."""
import copy
from datetime import date

from agents.extractor import parse_events
from agents.normalizer import normalize, parse_date
from agents.reasoner import categorize
from agents.synthesizer import to_row
from agents.validator import validate
from pipeline import build_graph
from tests.sample_events import SAMPLE_EVENTS_RAW, sample_state


def run_offline(**overrides):
    return build_graph(skip_until="normalizer").invoke(sample_state(**overrides))


def test_parse_events_handles_bad_model_output():
    assert parse_events("not json", "u") == []
    assert parse_events('{"events": "oops"}', "u") == []
    events = parse_events('{"events": [{"title": "A", "link": ""}]}', "https://src")
    assert events[0]["link"] == "https://src" and events[0]["source"] == "https://src"


def test_dates_in_several_formats():
    assert parse_date("2026-11-08") == date(2026, 11, 8)
    assert parse_date("November 8, 2026") == date(2026, 11, 8)
    assert parse_date("sometime in December") is None


def test_duplicates_merge_and_keep_the_detailed_copy():
    state = normalize({"events_raw": copy.deepcopy(SAMPLE_EVENTS_RAW)})
    markets = [e for e in state["events_clean"] if "Vintage" in e["title"]]
    assert len(markets) == 1 and markets[0]["time"] == "10am"
    assert state["duplicates_removed"] == 1


def test_every_event_is_published_or_reviewed_with_a_reason():
    result = run_offline()
    reasons = {e["title"]: e["review_reasons"] for e in result["events_review"]}
    filtered = {e["title"]: e["filter_reason"] for e in result["events_filtered"]}
    assert filtered["Seattle Symphony Open Rehearsal"] == "price listed: $15"
    assert reasons["Halloween Pumpkin Walk"] == ["already happened"]
    assert reasons["Ballard Night Market"] == ["missing venue"]
    assert reasons["Winter Lights Preview"] == ["date not understood"]
    total = len(result["events_valid"]) + len(result["events_review"]) + len(result["events_filtered"])
    assert total == len(SAMPLE_EVENTS_RAW) - 1


def test_include_paid_keeps_paid_events():
    result = run_offline(free_only=False)
    assert "Seattle Symphony Open Rehearsal" in {e["title"] for e in result["events_valid"]}


def test_categories():
    assert categorize({"title": "DJs in a Dive Bar"}) == "Music"
    assert categorize({"title": "Hidden Door Comedy"}) == "Comedy"
    assert categorize({"title": "Book swap"}) == "Community"


def test_picks_are_capped_per_month_and_varied():
    result = run_offline(max_picks=3, window_days=90)
    picks = [e for e in result["events_valid"] if e["pick_suggested"] and e["date"].month == 11]
    assert len(picks) == 3
    assert any(e["pick_suggested"] for e in result["events_valid"] if e["date"].month == 12)
    assert max(sum(p["category"] == c for p in picks) for c in {p["category"] for p in picks}) <= 2


def test_rows_match_the_sheet_columns():
    row = to_row({"title": "X", "date": date(2026, 11, 7), "venue": "V", "category": "Art"})
    assert list(row) == ["title", "date", "time", "spot", "hood", "cat", "desc", "cost", "link", "pick"]
    assert row["date"] == "November 7" and row["pick"] == "FALSE"


def test_trace_accounts_for_every_pulled_event():
    result = run_offline()
    trace = result["trace"]
    assert len(trace) == len(SAMPLE_EVENTS_RAW)
    assert {t["id"] for t in trace} == {f"e{i:03d}" for i in range(1, len(SAMPLE_EVENTS_RAW) + 1)}
    statuses = {t["title"]: t["status"] for t in trace}
    assert statuses["Halloween Pumpkin Walk"] == "Needs review"
    dup = [t for t in trace if t["status"] == "Duplicate"][0]
    kept = [t for t in trace if t["id"] == dup["merged_into"]][0]
    assert kept["time"] == "10am" and kept["status"] in ("Pick", "Publish")


def test_every_choice_has_a_reason():
    for t in run_offline(max_picks=3)["trace"]:
        assert t["why"], t["title"]


def test_custom_events_go_through_the_same_steps():
    custom = [
        {"custom_id": "c-1", "title": "Seattle Unlocked Dinner Club", "date": "2026-11-07",
         "time": "7pm", "venue": "Capitol Hill loft", "neighborhood": "Capitol Hill",
         "cost": "$35", "description": "A small sponsored dinner.", "link": "", "feature": True,
         "category": "Food & Drink"},
        {"custom_id": "c-2", "title": "Old Show", "date": "2026-10-01", "venue": "Somewhere",
         "cost": "Free"},
        # Same as a scraped event: yours wins, the scraped copy is merged.
        {"custom_id": "c-3", "title": "Hidden Door Comedy", "date": "2026-11-06", "time": "8:30pm",
         "venue": "The Door", "cost": "Free"},
    ]
    result = run_offline(custom_events=custom, max_picks=3)
    by_id = {t["id"]: t for t in result["trace"]}
    assert by_id["c-1"]["status"] == "Pick" and by_id["c-1"]["category"] == "Food & Drink"
    assert by_id["c-1"]["why"] == "added by you as a pick"  # paid is fine for your own events
    assert by_id["c-2"]["status"] == "Needs review"
    assert by_id["c-3"]["status"] in ("Pick", "Publish") and by_id["c-3"]["custom"]
    scraped = [t for t in result["trace"] if t["title"] == "Hidden Door Comedy" and not t["custom"]][0]
    assert scraped["status"] == "Duplicate"
    assert sum(t["status"] == "Pick" and t["date"].month == 11 for t in result["trace"]) == 3
    assert len(result["trace"]) == len(SAMPLE_EVENTS_RAW) + 3


def test_snapshot_round_trip(tmp_path, monkeypatch):
    import snapshot
    monkeypatch.setattr(snapshot, "PATH", tmp_path / "latest.json")
    assert snapshot.load() is None
    state = sample_state()
    snapshot.save(state)
    loaded = snapshot.load()
    assert len(loaded["events_raw"]) == len(SAMPLE_EVENTS_RAW)
    assert snapshot.fetched_on(loaded) is not None
    # A loaded snapshot runs through the rest of the pipeline like a fresh fetch.
    result = build_graph(skip_until="normalizer").invoke({**loaded, "today": state["today"]})
    assert len(result["trace"]) == len(SAMPLE_EVENTS_RAW)


def test_long_pages_are_read_in_overlapping_chunks():
    from agents.extractor import CHUNK_CHARS, CHUNK_OVERLAP, chunks
    text = "x" * (CHUNK_CHARS * 2 + 500)
    parts = chunks(text)
    assert len(parts) == 3 and all(len(p) <= CHUNK_CHARS for p in parts)
    assert parts[0][-CHUNK_OVERLAP:] == parts[1][:CHUNK_OVERLAP]
    assert chunks("") == []


def test_real_estate_events_are_filtered_out_but_recorded():
    from agents.validator import blocked_topic
    assert blocked_topic({"title": "Bellevue Real Estate Seminar"}).startswith("real estate")
    assert blocked_topic({"title": "DADU 101: Unlock Your Backyard's Potential"})
    assert blocked_topic({"title": "Free class", "description": "Talk with a local Realtor about escrow"})
    assert blocked_topic({"title": "Fremont Vintage Market"}) is None
    assert blocked_topic({"title": "Readers' book club"}) is None  # "read" is not "realty"

    extra = [{"title": "First-Time Homebuyer Workshop", "date": "2026-11-10", "venue": "Library",
              "cost": "Free", "source": "https://x.com"}]
    state = sample_state()
    state["events_raw"] = state["events_raw"] + [{**extra[0], "id": "e999"}]
    result = build_graph(skip_until="normalizer").invoke(state)
    t = [t for t in result["trace"] if t["id"] == "e999"][0]
    assert t["status"] == "Filtered" and "real estate" in t["why"]
    assert "First-Time Homebuyer Workshop" not in {r["title"] for r in result["rows"]}

    # Events you add yourself are never filtered.
    mine = build_graph(skip_until="normalizer").invoke(
        sample_state(custom_events=[{**extra[0], "custom_id": "c-9"}]))
    assert [t for t in mine["trace"] if t["id"] == "c-9"][0]["status"] != "Filtered"


def test_monthly_pages_roll_over_the_year():
    from config import month_pages
    assert month_pages(date(2026, 11, 5)) == [
        "https://www.events12.com/seattle/november/",
        "https://www.events12.com/seattle/december/",
        "https://www.events12.com/seattle/january/",
    ]


def test_paid_or_ticketed_events_never_reach_the_list():
    from agents.validator import paid_reason
    assert paid_reason({"cost": "$45"}) == "price listed ($45)"
    assert paid_reason({"cost": "Free", "ticketed": True}).startswith("tickets required")
    assert paid_reason({"cost": "Not listed", "description": "Buy tickets at the door"})
    assert paid_reason({"cost": "Free", "description": "Tickets from $20"})
    assert paid_reason({"cost": "Free", "description": "Free, RSVP required"}) is None

    base = {"date": "2026-11-10", "venue": "Hall", "source": "https://x.com"}
    state = sample_state()
    state["events_raw"] = state["events_raw"] + [
        {**base, "id": "p1", "title": "Big Concert", "cost": "", "description": "Get tickets now"},
        {**base, "id": "p2", "title": "Mystery Show", "cost": ""},
    ]
    result = build_graph(skip_until="normalizer").invoke(state)
    by = {t["id"]: t for t in result["trace"]}
    assert by["p1"]["status"] == "Filtered"
    assert by["p2"]["status"] == "Needs review" and "cost not listed" in by["p2"]["why"]
    assert not {"Big Concert", "Mystery Show"} & {r["title"] for r in result["rows"]}


def test_ontology_links_every_event_to_its_things():
    import ontology
    result = run_offline()
    graph = ontology.build(result["trace"])
    types = {n["type"] for n in graph["nodes"]}
    assert {"Event", "Category", "Venue", "Neighborhood", "Source", "Month", "Status"} <= types
    events = [n for n in graph["nodes"] if n["type"] == "Event"]
    assert len(events) == len(result["trace"])
    rels = {e["rel"] for e in graph["edges"]}
    assert {"IS_A", "HAPPENS_AT", "IN_AREA", "FOUND_ON", "IN_MONTH", "DUPLICATE_OF"} <= rels
    sm = ontology.summary(graph)
    assert sm["sources"] and sm["categories"]
    # The merged Fremont copy points at the kept event, so the kept one isn't "only here".
    dup = [e for e in graph["edges"] if e["rel"] == "DUPLICATE_OF"][0]
    assert dup["target"].startswith("Event:")


def test_filters_are_editable_and_allow_list_survives_reruns(tmp_path, monkeypatch):
    import filters
    import kvstore
    monkeypatch.setattr(kvstore, "DATA", tmp_path)
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    kvstore._cache.clear()
    rules = filters.load()
    # Turn off the price rule: the $15 rehearsal is no longer filtered.
    rules["price_listed"] = False
    result = run_offline(filters=rules)
    assert "Seattle Symphony Open Rehearsal" not in {e["title"] for e in result["events_filtered"]}
    # Add a new topic: anything about yoga is filtered, with that category.
    rules = filters.load()
    rules["topics"]["Fitness classes"] = ["yoga"]
    result = run_offline(filters=rules)
    yoga = [e for e in result["events_filtered"] if e["title"] == "Rooftop Sunset Yoga"][0]
    assert yoga["filter_category"] == "Fitness classes"
    # Allow one event by its stable key: it comes back on the list.
    rules["allow"] = [yoga["filter_key"]]
    result = run_offline(filters=rules)
    assert "Rooftop Sunset Yoga" in {e["title"] for e in result["events_valid"]}
    # Saved rules round-trip.
    filters.save(rules)
    assert filters.load()["topics"]["Fitness classes"] == ["yoga"]


def test_curator_uses_the_operating_point():
    result = run_offline(window_days=90)
    by = {t["title"]: t for t in result["trace"]}
    assert by["Seattle AI Builders Meetup"]["status"] in ("Pick", "Publish")
    assert by["Free AI Webinar: Grow Your Business 10x"]["status"] == "Filtered"
    assert by["Free AI Webinar: Grow Your Business 10x"]["filter_category"] == "AI: low relevance"
    assert by["Free Wealth Building Workshop"]["ai_intent"] == "Sales funnel"
    tool = by["Neighborhood Tool Library Open Hours"]
    assert tool["status"] == "Needs review" and "AI unsure (58)" in tool["why"]
    # Lowering the bar keeps the borderline event; raising it holds more.
    assert {t["title"]: t for t in run_offline(window_days=90, keep_at=50)["trace"]}[
        "Neighborhood Tool Library Open Hours"]["status"] in ("Pick", "Publish")
    assert {t["title"]: t for t in run_offline(window_days=90, keep_at=85)["trace"]}[
        "Rooftop Sunset Yoga"]["status"] == "Needs review"


def test_team_votes_override_the_model():
    import filters
    from agents.normalizer import parse_date
    key = filters.event_key({"title": "Free Wealth Building Workshop", "date": parse_date("2026-11-14")})
    meetup = filters.event_key({"title": "Seattle AI Builders Meetup", "date": parse_date("2026-11-12")})
    rows = [{"event_key": key, "vote": 1, "title": "x"}, {"event_key": meetup, "vote": -1, "title": "y"}]
    by = {t["title"]: t for t in run_offline(window_days=90, feedback_rows=rows)["trace"]}
    assert by["Free Wealth Building Workshop"]["status"] in ("Pick", "Publish")
    assert by["Seattle AI Builders Meetup"]["filter_category"] == "Downvoted by team"


def test_live_curation_calls_the_model_once_per_new_event(monkeypatch):
    from agents import curator
    calls = []

    def fake(batch, examples):
        calls.append((len(batch), len(examples)))
        return {e["key"]: {"intent": "Community gathering", "score": 90, "reason": "ok",
                           "version": curator.PROMPT_VERSION}
                for e in batch}
    monkeypatch.setattr(curator, "classify_batch", fake)
    rows = [{"event_key": "a|b", "vote": -1, "title": "Bad pitch", "created_at": "1"}]
    state = sample_state(window_days=90, curate_live=True, curation={}, feedback_rows=rows)
    first = build_graph(skip_until="normalizer").invoke(state)
    assert calls and all(n_examples == 1 for _, n_examples in calls)
    n = len(calls)
    build_graph(skip_until="normalizer").invoke(
        sample_state(window_days=90, curate_live=True, curation=first["curation"], feedback_rows=rows))
    assert len(calls) == n  # everything was cached


def test_feedback_store_and_few_shot_prompt(tmp_path, monkeypatch):
    import feedback
    from agents.curator import build_messages, parse
    monkeypatch.setattr(feedback, "PATH", tmp_path / "fb.json")
    ev = {"key": "k1", "title": "Crypto Seminar", "description": "Free pizza, learn to trade", "venue": "Hall"}
    feedback.vote(ev, -1, {"score": 65, "intent": "Free class or talk"}, note="sales pitch")
    feedback.vote({**ev, "key": "k2", "title": "Park Cleanup"}, 1)
    feedback.vote(ev, -1, note="sales pitch")  # re-vote replaces, doesn't duplicate
    rows = feedback.load()
    assert len(rows) == 2 and feedback.votes_by_key(rows) == {"k1": -1, "k2": 1}
    system = build_messages([{"key": "z", "title": "t"}], feedback.few_shots(rows))[0]["content"]
    assert 'DO NOT FEATURE: "Crypto Seminar"' in system and "sales pitch" in system
    assert 'FEATURE: "Park Cleanup"' in system
    parsed = parse('{"results": [{"key": "z", "intent": "Nope", "score": 140, "reason": "r"}]}', ["z"])
    assert parsed["z"]["score"] == 100 and parsed["z"]["intent"] == "Vague or low effort"
    assert parse("not json", ["z"]) == {}
    labeled = parse('{"results": [{"key": "z", "intent": "Arts and culture", "score": 80, "reason": "r",'
                    ' "label": "  Sunset   Photo Walk Downtown "}]}', ["z"])
    assert labeled["z"]["label"] == "Sunset Photo Walk"  # trimmed to 3 words
    assert parsed["z"]["label"] == ""  # missing label is fine


def test_religious_and_partisan_events_are_filtered_but_cultural_festivals_stay():
    by = {t["title"]: t for t in run_offline(window_days=90)["trace"]}
    assert by["Sunday Revival Worship Night"]["filter_category"] == "AI: low relevance"
    assert by["Sunday Revival Worship Night"]["ai_intent"] == "Religious service"
    assert by["Candidate Meet and Greet"]["ai_intent"] == "Divisive or partisan"
    assert by["Candidate Meet and Greet"]["status"] == "Filtered"
    assert by["Diwali Festival of Lights"]["status"] in ("Pick", "Publish")
    assert by["MLK Day March and Rally"]["status"] in ("Pick", "Publish")


def test_prompt_states_the_policy_and_old_scores_get_rescored(monkeypatch):
    from agents import curator
    system = " ".join(curator.build_messages([], [])[0]["content"].split())
    for phrase in ("community", "Religious services", "Divisive or partisan", "Treat every side the same way",
                   "Diwali", "Salesy"):
        assert phrase in system
    seen = []
    monkeypatch.setattr(curator, "classify_batch",
                        lambda batch, ex: seen.extend(e["key"] for e in batch) or {})
    old = {k: {**v, "version": "curator-v1"} for k, v in sample_state()["curation"].items()}
    build_graph(skip_until="normalizer").invoke(sample_state(window_days=90, curate_live=True, curation=old))
    assert set(old) <= set(seen) or len(seen) >= len(old) - 2  # v1 scores are re-scored


def test_curator_prompt_names_the_audience():
    from agents.curator import AUDIENCE, build_messages
    system = " ".join(build_messages([], [])[0]["content"].split())
    assert "adults 28 to 52" in system and "sales pitches" in system
    assert len(AUDIENCE["traits"]) == 5
