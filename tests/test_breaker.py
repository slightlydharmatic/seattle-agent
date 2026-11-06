"""Circuit breaker: a broken run must never replace the public list."""
import breaker


def ev(n, site="everout.com"):
    return [{"title": f"e{i}", "source": f"https://www.{site}/page"} for i in range(n)]


def snap(*parts, pages=10, failed=0):
    events = [e for p in parts for e in p]
    return {"events_raw": events, "source_urls": [f"u{i}" for i in range(pages)],
            "pages_failed": [f"u{i}" for i in range(failed)]}


def test_normal_run_passes():
    old = snap(ev(20), ev(10, "do206.com"))
    new = snap(ev(18), ev(12, "do206.com"))
    r = breaker.check(new, old)
    assert not r["tripped"] and not r["warnings"]


def test_trips_when_events_collapse():
    r = breaker.check(snap(ev(8)), snap(ev(40)))
    assert r["tripped"] and "less than half" in r["reasons"][0]


def test_trips_on_empty_run():
    assert breaker.check(snap(), snap(ev(30)))["tripped"]


def test_trips_when_most_pages_fail():
    r = breaker.check(snap(ev(30), pages=10, failed=7), snap(ev(30)))
    assert r["tripped"] and "pages failed" in r["reasons"][0]


def test_one_quiet_source_warns_but_does_not_trip():
    old = snap(ev(15), ev(10, "do206.com"), ev(5, "seattlecenter.org"))
    new = snap(ev(20), ev(12, "do206.com"))
    r = breaker.check(new, old)
    assert not r["tripped"] and "seattlecenter.org" in r["warnings"][0]


def test_trips_when_ai_filters_most_events():
    curated = {"events_valid": [{"ai": {"score": 90}}] * 3,
               "events_review": [],
               "events_filtered": [{"filter_category": "AI: low relevance"}] * 12}
    r = breaker.check(snap(ev(30)), snap(ev(30)), curated)
    assert r["tripped"] and "AI filtered out 12 of 15" in r["reasons"][0]


def test_small_baseline_is_not_judged():
    assert not breaker.check(snap(ev(2)), snap(ev(6)))["tripped"]


def test_hold_and_clear(tmp_path, monkeypatch):
    monkeypatch.setattr(breaker, "HELD", tmp_path / "held.json")
    breaker.hold({"events_raw": []}, {"tripped": True, "reasons": ["x"]})
    assert breaker.held()["breaker"]["reasons"] == ["x"]
    breaker.clear()
    assert breaker.held() is None
