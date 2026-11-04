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
    assert reasons["Seattle Symphony Open Rehearsal"] == ["not free ($15)"]
    assert reasons["Halloween Pumpkin Walk"] == ["already happened"]
    assert reasons["Ballard Night Market"] == ["missing venue"]
    assert reasons["Winter Lights Preview"] == ["date not understood"]
    assert len(result["events_valid"]) + len(result["events_review"]) == len(SAMPLE_EVENTS_RAW) - 1


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
