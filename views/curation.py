"""How it works: the case study page (hero phone, system diagram, costs, decisions) plus team controls."""
from datetime import date
from urllib.parse import urlparse

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

import costs
import feedback
import filters
from agents.curator import INTENTS, LOW_VALUE, PROMPT_VERSION, build_messages
from agents.synthesizer import MERGED, PICK, PUBLISH
from config import CURATOR_MODEL, MONTHLY_PAGES, OPENAI_MODEL, SOURCE_PAGES
from ui import flow, hero, howitworks
from ui.nav import go_to


def render(ctx) -> None:
    team, raw, trace, fb_rows = ctx.team, ctx.raw, ctx.trace, ctx.fb_rows
    rules = filters.load()
    op = rules.get("curation", {"keep_at": 70, "drop_below": 40})
    lo, hi = op["drop_below"], op["keep_at"]

    scored = trace[trace["ai_score"].notna()]
    decided = trace[trace["status"] != MERGED]
    n_kept = int(((decided["ai_score"] >= hi) & decided["status"].isin([PICK, PUBLISH])).sum())
    n_unsure = int(decided["why"].astype(str).str.startswith("AI unsure").sum())
    n_low = int((decided["filter_category"] == "AI: low relevance").sum())

    raw_events = (raw or {}).get("events_raw") or []
    n_sites = len({urlparse(e.get("source") or "").netloc for e in raw_events} - {""}) or len(SOURCE_PAGES) + len(MONTHLY_PAGES)
    # Eval metrics for the case study (precision / recall need 10+ labeled votes)
    labeled = [r for r in fb_rows if r.get("model_score") is not None]
    cs_metrics = {"votes": len(labeled),
                  "close_share": (n_unsure / len(scored)) if len(scored) else None}
    if len(labeled) >= 10:
        kept_lab = [r for r in labeled if int(r["model_score"]) >= hi]
        good = [r for r in labeled if int(r["vote"]) > 0]
        cs_metrics["precision"] = (sum(int(r["vote"]) > 0 for r in kept_lab) / len(kept_lab)) if kept_lab else None
        cs_metrics["recall"] = (sum(int(r["model_score"]) >= hi for r in good) / len(good)) if good else None

    # Hero: the phone with this week's picks and our real posts
    live = trace[trace["status"].isin([PICK, PUBLISH])].copy()
    live["_p"] = (live["status"] != PICK).astype(int)
    live["_d"] = live["date"].map(lambda d: d if isinstance(d, date) else date.max)
    live = live[live["_d"] >= date.today()] if (live["_d"] >= date.today()).any() else live
    picks = live.sort_values(["_p", "_d"]).head(8).to_dict("records")
    components.html(hero.render(picks), height=hero.HEIGHT)

    posts = hero.load_posts()
    views = hero.short(sum(p.get("views", 0) for p in posts)) if posts else "80k"
    est = costs.estimate(len((raw or {}).get("source_urls") or []) or 20, len(trace), OPENAI_MODEL, CURATOR_MODEL)

    def m(v):
        return howitworks.money(v)
    found = len(raw_events)
    n_picks = int((decided["status"] == PICK).sum())
    judged = not scored.empty

    def pct(x):
        return f"{x:.0%}" if isinstance(x, (int, float)) else "—"
    green, amber, red = ("#E6F2EC", "#2F6B53"), ("#F8EDD6", "#7A5A16"), ("#F8E4E1", "#A8423A")
    nodes = [
        {"id": "find", "col": 1, "row": 1, "step": "01", "title": "Sources", "sub": "Choose trusted sources, pull every listing",
         "specs": [["tool", "search"], ["cost", "~1 credit/pg"]],
         "more": "We decide which sources to trust, like event sites and city calendars. Every week an agent pulls every listing from them."},
        {"id": "read", "col": 2, "row": 1, "step": "02", "title": "Extractor", "sub": "Turn messy pages into clean events", "ai": True,
         "specs": [["model", OPENAI_MODEL], ["cost", f"{m(est['extract']['usd'])}/run"], ["speed", "batch"],
                   ["why", "volume"]], "img": "steps/s2.png",
         "more": "Cheapest model that's good enough: it only pulls out title, date, place, cost, and link. Repeats are merged."},
        {"id": "rules", "col": 3, "row": 1, "step": "03", "title": "Rules", "sub": "Drop paid, ticketed, and off-topic events",
         "specs": [["model", "none"], ["cost", "$0"]],
         "more": "Simple rules run before any AI, so we never pay a model to look at an obvious no."},
        {"id": "judge", "col": 4, "row": 1, "step": "04", "title": "AI judge", "sub": "Score each event for our readers", "ai": True,
         "specs": [["model", CURATOR_MODEL], ["cost", f"{m(est['curate']['usd'])}/run"], ["speed", "batch, cached"],
                   ["why", "quality"]], "img": "steps/s3.png",
         "more": "Reads what each event is for, not its keywords. Returns an intent, a 0 to 100 score, and one line on why. "
                 "This is the step worth a stronger model; it's set up to swap one in."
                 + ("" if judged else " (This snapshot hasn't been scored yet.)")},
        {"id": "decide", "col": 5, "row": 1, "step": "05", "title": "Threshold", "sub": "Set the bar for going live",
         "band": [[f"{hi}+ live", *green], [f"{lo}–{hi - 1} us", *amber], [f"<{lo} out", *red]],
         "specs": [["precision", f"{hi}+ live"], ["recall", f"{lo}–{hi - 1} → us"]],
         "more": "Tuned for precision: one spammy pick costs more trust than a missed event. "
                 "The middle band goes to people, so good borderline events aren't lost (that protects recall)."},
        {"id": "publish", "col": 6, "row": 1, "step": "06", "title": "Snapshot", "sub": "Save the weekly list for readers", "img": "steps/s1.png",
         "specs": [["cost", "$0"], ["speed", "instant"]],
         "more": "Readers load a saved snapshot, so the public page is instant and never calls a paid API."},
        {"id": "validate", "col": 2, "row": 2, "lane": "guard", "title": "Validator", "sub": "Hold events missing a date or place",
         "tag": "no AI", "tagc": "free"},
        {"id": "memory", "col": 4, "row": 2, "lane": "guard", "title": "Memory", "sub": "Feed our latest votes back as examples",
         "tag": "12 latest votes", "more": "8 recent thumbs down and 4 thumbs up are added to the judge's instructions every run."},
        {"id": "breaker", "col": 6, "row": 2, "lane": "guard", "title": "Circuit breaker", "sub": "Hold any run that looks broken",
         "tag": "no AI", "tagc": "free",
         "more": "Holds a run if events halve, most pages fail, sources go quiet, or the AI drops 60%+. Readers keep last week's list."},
        {"id": "evals", "col": 3, "row": 3, "lane": "guard", "title": "Evals", "sub": "Grade the AI against our votes",
         "specs": [["precision", pct(cs_metrics.get("precision"))], ["recall", pct(cs_metrics.get("recall"))]],
         "more": "Every vote is a label. Next: a hand-labeled test set every prompt change has to pass."},
        {"id": "team", "col": 5, "row": 3, "lane": "human", "title": "Team review", "sub": "Make the close calls",
         "tag": "people", "tagc": "ppl", "img": "steps/s4.png", "more": "A vote overrides the AI right away."},
        {"id": "post", "col": 6, "row": 3, "lane": "human", "title": "Instagram", "sub": "Design and post the picks",
         "tag": "people", "tagc": "ppl", "img": "posts/01-january.jpg" if posts else None,
         "more": "The AI never posts. People design and publish the list."},
    ]
    edges = [("find", "read"), ("read", "rules"), ("rules", "judge"), ("judge", "decide"), ("decide", "publish"),
             ("read", "validate"), ("memory", "judge"), ("decide", "team", "close calls"), ("publish", "breaker"),
             ("breaker", "post")]
    loops = [("team", "memory", "votes become examples"), ("team", "evals", "votes grade the AI")]
    st.markdown(howitworks.CSS + howitworks.top(n_sites, est, views, found, n_picks), unsafe_allow_html=True)
    components.html(flow.render(nodes, edges, loops), height=flow.HEIGHT)

    examples = [("Free AI Webinar: Grow Your Business 10x", "Sales pitch", 14, False),
                ("Seattle AI Builders Meetup", "Real meetup", 86, True),
                ("Sunday Revival Worship Night", "Religious service", 8, False),
                ("Diwali Festival of Lights", "Community festival", 92, True)]
    st.markdown(howitworks.calls(hi, lo, cs_metrics, examples) + howitworks.broke(),
                unsafe_allow_html=True)

    if not team:
        return
    st.markdown("<div class='hw'><div class='hw-h'><div class='h2'>Team <em>controls</em></div><span>only visible when signed in</span></div></div>",
                unsafe_allow_html=True)
    # This week's numbers
    st.markdown(f"""
<div class='ob ob-sec cute'><span class='t'>This week's numbers</span></div>
<div class='ob band'>
  <div class='seg lo' style='flex:{lo}'><b>{n_low}</b><span>Filtered · under {lo}</span></div>
  <div class='seg mid' style='flex:{hi - lo}'><b>{n_unsure}</b><span>Team reviews · {lo} to {hi - 1}</span></div>
  <div class='seg hi' style='flex:{100 - hi}'><b>{n_kept}</b><span>On the list · {hi}+</span></div>
</div>""", unsafe_allow_html=True)
    if scored.empty:
        st.caption("No AI scores yet. " + ("Press Re-curate with AI in the sidebar." if team
                                           else "They appear after the next weekly refresh."))
    if team:
        with st.expander("Adjust the cutoffs"):
            with st.form("op", border=False):
                keep_at, drop_below = st.slider("Filter below, keep at", 0, 100, (lo, hi), step=5)
                st.caption("Higher keep line: fewer bad picks, more events for the team to review.")
                if st.form_submit_button("Save", type="primary"):
                    rules["curation"] = {"keep_at": keep_at, "drop_below": drop_below}
                    filters.save(rules)
                    st.rerun()

    # 4. How well it's working
    st.markdown("<div class='ob ob-sec cute'><span class='t'>How well it's working</span></div>", unsafe_allow_html=True)
    if len(labeled) < 10:
        teach_empty(len(labeled), team)
    else:
        import altair as alt
        lab = pd.DataFrame({"score": [int(r["model_score"]) for r in labeled],
                            "good": [int(r["vote"]) > 0 for r in labeled]})
        pts = []
        for th in range(0, 101, 5):
            kept = lab[lab["score"] >= th]
            prec = kept["good"].mean() if len(kept) else None
            rec = kept["good"].sum() / max(lab["good"].sum(), 1)
            pts += [{"threshold": th, "metric": "Precision", "value": prec},
                    {"threshold": th, "metric": "Recall", "value": rec}]
        curve = pd.DataFrame(pts).dropna()
        at = curve[curve["threshold"] == hi // 5 * 5].set_index("metric")["value"]
        c1, c2, c3 = st.columns(3)
        c1.metric("Picks the team agrees with", f"{at.get('Precision', 0):.0%}", help="Precision at the keep line")
        c2.metric("Good events the AI found", f"{at.get('Recall', 0):.0%}", help="Recall at the keep line")
        c3.metric("Votes", len(lab))
        line = alt.Chart(curve).mark_line(point=True).encode(
            x=alt.X("threshold:Q", title="Keep line (AI score)"),
            y=alt.Y("value:Q", title=None, axis=alt.Axis(format="%"), scale=alt.Scale(domain=[0, 1])),
            color=alt.Color("metric:N", scale=alt.Scale(range=["#A04D74", "#5E8C7A"]), title=None))
        rule = alt.Chart(pd.DataFrame({"x": [hi]})).mark_rule(color="#D29A3A", strokeDash=[4, 4]).encode(x="x:Q")
        st.altair_chart((line + rule).properties(height=240), width="stretch")

    caught = trace[(trace["filter_category"] == "AI: low relevance")]
    if not caught.empty:
        st.markdown("<div class='ob ob-sec'><span class='t'>Caught by AI, missed by keywords</span>"
                    f"<span class='c'>{len(caught)}</span></div>", unsafe_allow_html=True)
        st.dataframe(pd.DataFrame({"Event": caught["title"], "AI says": caught["ai_intent"],
                                   "Score": caught["ai_score"].astype(int), "Why": caught["ai_reason"]}),
                     hide_index=True, width="stretch")

    # 5. Under the hood: for the team and the curious
    st.markdown("<div class='ob ob-sec cute'><span class='t'>Under the hood</span></div>", unsafe_allow_html=True)
    shots = feedback.few_shots(fb_rows)
    if not scored.empty:
        with st.expander("Events by intent"):
            by = scored.groupby("ai_intent")["ai_score"].agg(["count", "mean"]).reindex(INTENTS).dropna()
            by = by.reset_index().rename(columns={"ai_intent": "Intent", "count": "Events", "mean": "Avg score"})
            by["Avg score"] = by["Avg score"].round().astype(int)
            by["Events"] = by["Events"].astype(int)
            by["Value"] = by["Intent"].map(lambda i: "low" if i in LOW_VALUE else "high")
            st.dataframe(by, hide_index=True, width="stretch")
    with st.expander(f"What the AI is learning from · {len(shots)} votes"):
        if shots:
            st.code(feedback.few_shot_text(shots), language=None, wrap_lines=True)
        else:
            st.caption("The most recent thumbs are added to the AI's instructions as examples. None yet.")
    if team and fb_rows:
        with st.expander(f"All votes · {len(fb_rows)}"):
            log = pd.DataFrame([{"Vote": "▲" if int(r["vote"]) > 0 else "▼", "Event": r["title"],
                                 "AI score then": r.get("model_score"), "AI intent then": r.get("model_intent"),
                                 "Note": r.get("note", ""), "When": str(r.get("created_at", ""))[:10]}
                                for r in reversed(fb_rows)])
            st.dataframe(log, hide_index=True, width="stretch")
    with st.expander(f"The AI's full instructions · {PROMPT_VERSION}"):
        st.code(build_messages([], shots)[0]["content"], language=None, wrap_lines=True)


def teach_empty(n: int, team: bool) -> None:
    """Empty state for the precision/recall chart: one line, a progress bar, and the way to fill it."""
    need = 10
    st.markdown(
        "<div class='ob teach'><p class='teach-lead'>Vote on 10 events to see how often the AI agrees with you.</p>"
        f"<div class='teach-bar'><i style='width:{min(n, need) / need:.0%}'></i></div>"
        f"<p class='teach-count'>{n} of {need} votes</p></div>", unsafe_allow_html=True)
    if team:
        st.button("Start voting on events", type="primary", icon=":material/thumb_up:",
                  on_click=go_to, args=("events",))
