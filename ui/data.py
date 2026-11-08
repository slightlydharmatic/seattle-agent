"""Loading the run: snapshot or sample data, the pipeline's fast steps, votes, and the trace.

Everything a page needs comes back in one Ctx object, so views and helpers never read globals.
Not cached on purpose: votes, filters, and added events must show up the moment they change.
"""
import calendar
import os
from dataclasses import dataclass
from datetime import date, timedelta

import pandas as pd
import streamlit as st

import breaker
import custom_events
import feedback
import filters
import snapshot
from pipeline import build_graph
from tests.sample_events import sample_state
from ui.components import add_months, site


@dataclass
class Ctx:
    team: bool
    is_sample: bool
    as_of: date | None
    raw: dict
    months: list[date]
    labels: list[str]
    other: pd.DataFrame          # events outside the month range
    month_views: list[tuple]     # (nav label, count) for the End result sub-menu
    mine: list[dict]             # events added by hand
    fb_rows: list[dict]          # every vote
    res: dict                    # pipeline result
    votes: dict                  # event key -> +1 / -1
    trace: pd.DataFrame
    titles_by_id: dict


def fetch_live(query: str) -> dict:
    """Steps 1 to 2: the slow, paid part. Team only, and it saves a new snapshot."""
    raw = build_graph(stop_after="extractor").invoke({"query": query})
    old = snapshot.load()
    result = breaker.check(raw, old)
    if result["tripped"]:
        breaker.hold(snapshot.build(raw), result)  # readers keep the last good list
        return {}
    breaker.clear()
    snapshot.save(raw)
    return raw


def team_password() -> str:
    try:
        return str(st.secrets.get("TEAM_PASSWORD", "")) or os.getenv("TEAM_PASSWORD", "")
    except Exception:  # no secrets file locally
        return os.getenv("TEAM_PASSWORD", "")


def finish(raw: dict, custom: list[dict], end: date, picks: int, include_paid: bool,
           fb_rows: list[dict] | None = None, live: bool = False) -> dict:
    """Steps 3 to 7: fast, so they rerun whenever settings, votes, or your events change.

    The AI curator only calls the model when live=True (team buttons); otherwise it
    reuses the scores saved in the snapshot.
    """
    rules = filters.load()
    state = {**raw, "custom_events": custom, "window_end": end, "filters": rules,
             "max_picks": picks, "free_only": not include_paid, "curate_live": live,
             **rules.get("curation", {})}
    if fb_rows is not None:
        state["feedback_rows"] = fb_rows
    return build_graph(skip_until="normalizer").invoke(state)


def run_live_search(query: str) -> dict | None:
    """Team's "Run live search" button. Returns the snapshot to use next."""
    with st.spinner("Reading listing pages..."):
        try:
            fetched = fetch_live(query)
        except RuntimeError as err:  # missing keys, no credits, and similar setup problems
            st.error(str(err))
            st.stop()
    if not fetched.get("events_raw"):
        st.warning("The circuit breaker held that run, so readers still see the last good list. "
                   "Details are at the top of the Events page.")
    st.session_state.curate_now = "new"
    return snapshot.load()


def run_curation(snap: dict | None) -> dict | None:
    """Team: score events with the AI curator (new ones, or everything again with the latest votes)."""
    if st.session_state.pop("curate_now", None) and snap is not None:
        mode = st.session_state.pop("curate_mode", "new")
        base = {**snap, "curation": {} if mode == "all" else (snap.get("curation") or {})}
        with st.spinner("The AI curator is reading the events..."):
            try:
                done = finish(base, custom_events.load(), date.today().replace(day=28) + timedelta(days=95),
                              6, False, live=True)
                snapshot.save({**snap, "curation": done["curation"]})
                snap = snapshot.load()
                st.toast(f"Curated {len(done['curation'])} events")
            except RuntimeError as err:
                st.error(str(err))
    return snap


def load_ctx(snap: dict | None, use_sample: bool, n_months: int, picks: int, include_paid: bool, team: bool) -> Ctx:
    if use_sample or snap is None:
        raw, as_of, is_sample = sample_state(), None, True
    else:
        raw, as_of, is_sample = snap, snapshot.fetched_on(snap), False

    today = raw.get("today") if is_sample else date.today()
    months = [add_months(today.replace(day=1), i) for i in range(n_months)]
    last = months[-1]
    end = last.replace(day=calendar.monthrange(last.year, last.month)[1])

    mine = custom_events.load()
    fb_rows = feedback.load()
    res = finish(raw, mine, end, picks, include_paid, fb_rows=fb_rows)
    votes = feedback.votes_by_key(fb_rows)
    trace = pd.DataFrame(res["trace"])
    trace["month"] = trace["date"].map(lambda d: (d.year, d.month) if isinstance(d, date) else None)
    trace["site"] = trace.apply(lambda t: "added by you" if t["custom"] else site(t["source"]), axis=1)
    titles_by_id = dict(zip(trace["id"], trace["title"]))

    labels = [f"{m:%B %Y}" for m in months]
    in_range = {(m.year, m.month) for m in months}
    other = trace[~trace["month"].isin(in_range)]
    month_views = [(lab, int((trace["month"] == (m.year, m.month)).sum())) for lab, m in zip(labels, months)]
    if not other.empty:
        month_views.append(("Past or undated", len(other)))
    if mine:
        month_views.append(("Added by you", len(mine)))
    return Ctx(team=team, is_sample=is_sample, as_of=as_of, raw=raw, months=months, labels=labels, other=other,
               month_views=month_views, mine=mine, fb_rows=fb_rows, res=res, votes=votes, trace=trace,
               titles_by_id=titles_by_id)
