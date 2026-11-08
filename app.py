"""Seattle Unlocked event desk: every event pulled, where it came from, and what's live, by month.

    streamlit run app.py
"""
import hmac
from collections import Counter
from datetime import date
from urllib.parse import urlparse

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

import custom_events
import feedback
import breaker
from config import CURATOR_MODEL, MONTHLY_PAGES, OPENAI_MODEL, SOURCE_PAGES
import costs
import flow
import hero
import howitworks
import filters
from agents.curator import INTENTS, LOW_VALUE, PROMPT_VERSION, build_messages
import snapshot
from agents.reasoner import CATEGORIES
from agents.synthesizer import FILTERED, MERGED, PICK, PUBLISH, REVIEW, SHEET_COLUMNS
from ui import data, theme
from ui.components import day_label, esc, event_row, filtered_row, sheet_rows, site
from views import ontology as ontology_view

st.set_page_config(page_title="Seattle Unlocked · Event Desk", layout="wide")

theme.inject()


CATEGORY_OPTIONS = ["Auto"] + list(CATEGORIES) + ["Community"]


# ---------- data ----------


@st.dialog("Add an event")
def add_event_dialog() -> None:
    with st.form("add_event", border=False):
        title = st.text_input("Event name *")
        c1, c2 = st.columns(2)
        day = c1.date_input("Date *", value=date.today(), format="MM/DD/YYYY")
        time = c2.text_input("Time", placeholder="7pm")
        c3, c4 = st.columns(2)
        venue = c3.text_input("Venue *")
        hood = c4.text_input("Neighborhood", placeholder="Capitol Hill")
        c5, c6 = st.columns(2)
        category = c5.selectbox("Category", CATEGORY_OPTIONS)
        cost = c6.text_input("Cost", value="Free")
        desc = st.text_area("Description", height=80)
        link = st.text_input("Link", placeholder="https://")
        feature = st.checkbox("Feature it as a pick")
        if st.form_submit_button("Add event", type="primary", width="stretch"):
            if not title.strip() or not venue.strip():
                st.error("Add an event name and a venue.")
                return
            custom_events.add({
                "title": title.strip(), "date": day.isoformat(), "time": time.strip(),
                "venue": venue.strip(), "neighborhood": hood.strip(),
                "category": "" if category == "Auto" else category,
                "cost": cost.strip() or "Free", "description": desc.strip(),
                "link": link.strip(), "feature": feature,
            })
            st.rerun()


# ---------- sidebar ----------
team = st.session_state.get("team", False)
snap = snapshot.load()

with st.sidebar:
    st.markdown("<div class='ob ob-brand'><i></i>Seattle Unlocked</div>", unsafe_allow_html=True)
    nav_box = st.container(key="nav")  # filled in once the months are known
    st.divider()

    if team:
        use_sample = st.checkbox("Show sample data", value=snap is None)
        query = st.text_input("Search", "free events in Seattle")
        n_months = st.select_slider("Months", options=[1, 2, 3, 4], value=3)
        picks = st.slider("Picks per month", 0, 12, 6)
        include_paid = st.checkbox("Include paid events")
        go = st.button("Run live search", type="primary", width="stretch")
        if st.button("Re-curate with AI", width="stretch",
                     help="Score every event again using the latest thumbs up and down. Costs a few cents."):
            st.session_state.curate_now, st.session_state.curate_mode = True, "all"
        if st.button("Add an event", width="stretch"):
            add_event_dialog()
    else:
        use_sample, query, n_months, picks, include_paid, go = snap is None, "", 3, 6, False, False

if go:
    snap, use_sample = data.run_live_search(query), False

snap = data.run_curation(snap)
ctx = data.load_ctx(snap, use_sample, n_months, picks, include_paid, team)
raw, as_of, is_sample, months, mine = ctx.raw, ctx.as_of, ctx.is_sample, ctx.months, ctx.mine
fb_rows, res, votes, trace, titles_by_id = ctx.fb_rows, ctx.res, ctx.votes, ctx.trace, ctx.titles_by_id
labels, other, views = ctx.labels, ctx.other, ctx.month_views

with st.sidebar:
    pages = res.get("pages") or []
    ok = sum(p["status"] == "read" for p in pages)
    with st.expander(f"Pages read · {ok}/{len(pages)}"):
        for p in pages:
            st.write(f"{site(p['url'])} · {p['events'] if p['status'] == 'read' else p['status']}")
    st.caption("Sample data" if is_sample else f"Updated {as_of:%b} {as_of.day}, {as_of.year}" if as_of else "")
    if team:
        import kvstore
        if kvstore.is_connected():
            st.caption(":material/cloud_done: Team work saved to Supabase")
        else:
            st.caption(":material/warning: Votes and filter edits are saved on this server only "
                       "and reset when the app restarts. Connect Supabase to keep them.")

    st.divider()
    if team:
        if st.button("Sign out", width="stretch"):
            st.session_state.team = False
            st.rerun()
    else:
        with st.expander("Team sign in"):
            pw = st.text_input("Password", type="password", key="pw")
            if st.button("Sign in", width="stretch"):
                expected = data.team_password()
                if expected and hmac.compare_digest(pw, expected):
                    st.session_state.team = True
                    st.rerun()
                st.error("That password didn't work." if expected else "Sign in isn't set up yet.")

if is_sample:
    st.markdown("<div class='ob ob-note'>Sample data. These are example events, not live listings.</div>",
                unsafe_allow_html=True)


# ---------- pieces ----------


def record_table(df: pd.DataFrame, key: str) -> None:
    """Every event, where it came from, and which checks it passed."""
    if df.empty:
        st.markdown("<div class='ob empty'>No events this month yet.</div>", unsafe_allow_html=True)
        return
    def mark(t, name):
        for c in t["checks"] or []:
            if c["check"] == name:
                return "✓" if c["passed"] else "✕"
        return ""

    table = pd.DataFrame({
        "Status": df["status"],
        "Event": df["title"],
        "Date": df.apply(lambda t: day_label(t["date"]) if isinstance(t["date"], date)
                         else (t["date_as_listed"] or "No date"), axis=1),
        "Source": df["site"],
        "Title": df.apply(lambda t: mark(t, "Title"), axis=1),
        "Date ok": df.apply(lambda t: mark(t, "Date"), axis=1),
        "Venue": df.apply(lambda t: mark(t, "Venue"), axis=1),
        "Free": df.apply(lambda t: mark(t, "Free"), axis=1),
        "Why": df.apply(lambda t: f"same as {titles_by_id.get(t['merged_into'], '')}"
                        if t["status"] == MERGED else t["why"], axis=1),
        "Page": df.apply(lambda t: "" if t["custom"] else t["source"], axis=1),
    })
    color = {"✓": "color:#456F5E;font-weight:600", "✕": "color:#B14A40;font-weight:600"}
    styled = table.style.map(lambda v: color.get(v, ""), subset=["Title", "Date ok", "Venue", "Free"])
    st.dataframe(
        styled, hide_index=True, width="stretch", key=key,
        column_config={
            "Title": st.column_config.TextColumn("Title", width="small"),
            "Date ok": st.column_config.TextColumn("Date", width="small"),
            "Venue": st.column_config.TextColumn("Venue", width="small"),
            "Free": st.column_config.TextColumn("Free", width="small"),
            "Page": st.column_config.LinkColumn(display_text="open page", width="small"),
        },
    )


def cast_vote(t: dict, value: int) -> None:
    """Thumbs up/down. Clicking the same thumb again removes the vote."""
    if votes.get(t["key"]) == value:
        feedback.clear(t["key"])
    else:
        curation = {"score": t.get("ai_score"), "intent": t.get("ai_intent")}
        feedback.vote({**t, "description": t.get("description", "")}, value, curation)


def team_rows(group: pd.DataFrame, held: bool) -> None:
    for i, (_, t) in enumerate(group.iterrows(), 1):
        a, b, c = st.columns([24, 1, 1], gap="small", vertical_alignment="center")
        a.markdown(f"<div class='ob'>{event_row(i, t, held=held, votes=votes)}</div>", unsafe_allow_html=True)
        v = votes.get(t["key"])
        rec = t.to_dict()
        b.button("", icon=":material/thumb_up:", key=f"up-{t['key']}-{t['id']}", help="Feature events like this",
                 type="primary" if v == 1 else "tertiary", on_click=cast_vote, args=(rec, 1))
        c.button("", icon=":material/thumb_down:", key=f"dn-{t['key']}-{t['id']}", help="Don't feature events like this",
                 type="primary" if v == -1 else "tertiary", on_click=cast_vote, args=(rec, -1))


def render(df: pd.DataFrame, label: str, file_label: str | None) -> None:
    order = {PICK: 0, PUBLISH: 0, REVIEW: 1, MERGED: 2, FILTERED: 3}
    df = df.assign(_o=df["status"].map(order),
                   _d=df["date"].map(lambda d: d if isinstance(d, date) else date.max))
    df = df.sort_values(["_o", "_d", "title"])
    available = df[df["status"].isin([PICK, PUBLISH])]
    held = df[df["status"] == REVIEW]
    c = Counter(df["status"])
    sources = Counter(df.loc[df["status"] != MERGED, "site"])

    head = (f"{len(available)} free event{'s' if len(available) != 1 else ''}"
            + (f" · {c[PICK]} picks" if c[PICK] else ""))
    stats = ""
    if team:  # pipeline numbers are for the team; readers just get the list
        stats = (f"<div class='ob-stats'>"
                 f"<div class='ob-stat green'><span>Available</span><b>{len(available)}</b></div>"
                 f"<div class='ob-stat blue'><span>Picks</span><b>{c[PICK]}</b></div>"
                 f"<div class='ob-stat red'><span>Held</span><b>{c[REVIEW]}</b></div>"
                 f"<div class='ob-stat'><span>Duplicates</span><b>{c[MERGED]}</b></div>"
                 f"<a class='ob-stat link' href='#filtered-{abs(hash(label))}'><span>Filtered ↓</span><b>{c[FILTERED]}</b></a>"
                 f"<div class='ob-stat'><span>Sources</span><b>{len(sources)}</b></div></div>")
    st.markdown(
        f"<div class='ob'><div class='ob-head'><h2>{esc(label)}</h2><span class='ob-type'>{head}</span></div>"
        f"{stats}</div>", unsafe_allow_html=True)

    # 1. Available: one collapsible section, with a collapsible group per day
    st.write("")
    collapse = st.toggle("Collapse all days", key=f"collapse-{label}")
    day_open = "" if collapse else " open"
    body, n = "", 0
    for d, group in available.groupby("_d", sort=True):
        rows = ""
        for _, t in group.iterrows():
            n += 1
            rows += event_row(n, t, votes=votes)
        weekend = " weekend" if isinstance(d, date) and d.weekday() >= 5 else ""
        head = (f"<span class='wd'>{d:%a}</span>{d:%B} {d.day}" if isinstance(d, date) and d != date.max
                else "No date")
        body += (f"<details class='ob-acc-day'{day_open}><summary class='ob-day{weekend}'>"
                 f"<span class='chev'></span>{head}<span class='n'>{len(group)} event{'s' if len(group) != 1 else ''}</span></summary>"
                 f"{rows}</details>")
    if not body:
        body = "<div class='ob-empty-in'>No events ready for this month yet.</div>"
    if team:
        st.markdown(f"<div class='ob ob-sec' style='margin-top:18px'><span class='dot'></span>"
                    f"<span class='t'>Available</span><span class='c'>{len(available)}</span>"
                    f"<span class='hint'>thumbs teach the AI curator</span></div>", unsafe_allow_html=True)
        for d, group in available.groupby("_d", sort=True):
            label_d = f"{d:%a %B} {d.day}" if isinstance(d, date) and d != date.max else "No date"
            with st.expander(f"{label_d} · {len(group)} event{'s' if len(group) != 1 else ''}", expanded=not collapse):
                team_rows(group, held=False)
    else:
        st.markdown(f"<details class='ob ob-acc' open><summary class='ob-sec'><span class='chev'></span>"
                    f"<span class='dot'></span><span class='t'>Available</span><span class='c'>{len(available)}</span>"
                    f"</summary><div class='ob-list'>{body}</div></details>", unsafe_allow_html=True)

    if team and file_label and not available.empty:
        with st.expander("Sheet rows"):
            edited = st.data_editor(
                sheet_rows(available), hide_index=True, width="stretch", key=f"edit-{file_label}",
                column_config={"pick": st.column_config.CheckboxColumn("pick")},
                disabled=[col for col in SHEET_COLUMNS if col != "pick"])
            out = edited.assign(pick=edited["pick"].map({True: "TRUE", False: "FALSE"}))
            st.download_button(f"Download {file_label} - Seattle.csv", out.to_csv(index=False),
                               f"{file_label} - Seattle.csv", "text/csv", type="primary",
                               key=f"dl-{file_label}")

    # 2. Held: collapsible
    if team and not held.empty:
        with st.expander(f"Held for review · {len(held)}  (AI unsure and missing details)", expanded=not collapse):
            team_rows(held, held=True)
    rows = "".join(event_row(i, t, held=True, votes=votes) for i, (_, t) in enumerate(held.iterrows(), 1)) \
        or "<div class='ob-empty-in'>Nothing held.</div>"
    if not team or held.empty:
        st.markdown(f"<details class='ob ob-acc held'{'' if collapse else ' open'}><summary class='ob-sec held'>"
                    f"<span class='chev'></span><span class='dot'></span><span class='t'>Held for review</span>"
                    f"<span class='c'>{len(held)}</span></summary><div class='ob-list'>{rows}</div></details>",
                    unsafe_allow_html=True)

    # 3. Filtered out, grouped by reason
    filt = df[df["status"] == FILTERED]
    groups = ""
    for cat_name, grp in sorted(filt.groupby("filter_category"), key=lambda g: -len(g[1])):
        rows = "".join(filtered_row(t) for _, t in grp.iterrows())
        groups += (f"<details class='ob-acc-day'><summary class='ob-day filt'><span class='chev'></span>"
                   f"<span class='wd'>{esc(cat_name)}</span><span class='n'>{len(grp)} event{'s' if len(grp) != 1 else ''}</span></summary>"
                   f"{rows}</details>")
    groups = groups or "<div class='ob-empty-in'>Nothing filtered.</div>"
    st.markdown(f"<span id='filtered-{abs(hash(label))}'></span>"
                f"<details class='ob ob-acc'{'' if collapse else ' open'}><summary class='ob-sec filt'>"
                f"<span class='chev'></span><span class='dot'></span><span class='t'>Filtered out</span>"
                f"<span class='c'>{len(filt)}</span><span class='hint'>by reason"
                f"</span></summary><div class='ob-list'>{groups}</div></details>", unsafe_allow_html=True)

    ai_out = filt[filt["filter_category"].isin(["AI: low relevance", "Downvoted by team"])]
    if team and not ai_out.empty:
        with st.expander(f"Filtered by the AI or your team · {len(ai_out)}  (thumbs up to bring one back)"):
            team_rows(ai_out, held=True)

    # 4. Full record
    st.write("")
    with st.expander(f"Full record · {len(df)} events, every source and check", expanded=False):
        st.markdown("<div class='ob src-chips' style='border:none;padding:0 0 8px;background:none'>" + "".join(
            f"<span>{esc(s)}<b>{k}</b></span>" for s, k in sources.most_common()) + "</div>",
            unsafe_allow_html=True)
        record_table(df, key=f"rec-{label}")


# ---------- ontology ----------


# ---------- AI curation page ----------


def render_breaker() -> None:
    """Team only: a run the circuit breaker held back, with publish / discard."""
    h = breaker.held() if team else None
    if not h:
        return
    b, m = h["breaker"], h["breaker"]["metrics"]
    items = "".join(f"<li>{esc(r)}</li>" for r in b["reasons"])
    st.markdown(
        "<div class='ob breaker'><p class='br-lead'>Circuit breaker: the latest run was held back</p>"
        "<p>Readers still see the last good list. The new run looked broken:</p>"
        f"<ul>{items}</ul><p class='br-meta'>Checked {esc(b['checked_at'][:10])} · {m['events']} events found "
        f"(last time {m['events_last']}) · {m['pages_failed']} of {m['pages']} pages failed</p></div>",
        unsafe_allow_html=True)
    x, y, _ = st.columns([1, 1, 3])
    if x.button("Publish anyway", type="primary", help="Make the held run the public list."):
        snapshot.write(h["snapshot"])
        breaker.clear()
        st.rerun()
    if y.button("Discard held run"):
        breaker.clear()
        st.rerun()


def teach_empty(n: int) -> None:
    """Empty state for the precision/recall chart: one line, a progress bar, and the way to fill it."""
    need = 10
    st.markdown(
        "<div class='ob teach'><p class='teach-lead'>Vote on 10 events to see how often the AI agrees with you.</p>"
        f"<div class='teach-bar'><i style='width:{min(n, need) / need:.0%}'></i></div>"
        f"<p class='teach-count'>{n} of {need} votes</p></div>", unsafe_allow_html=True)
    if team:
        st.button("Start voting on events", type="primary", icon=":material/thumb_up:",
                  on_click=go_to, args=("events",))


def render_curation_page() -> None:
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
    st.markdown(howitworks.CSS + howitworks.top(n_sites, est, views), unsafe_allow_html=True)

    def m(v):
        return howitworks.money(v)
    green, amber, red = ("#E6F2EC", "#2F6B53"), ("#F8EDD6", "#7A5A16"), ("#F8E4E1", "#A8423A")
    nodes = [
        {"id": "find", "col": 1, "row": 1, "step": "01", "title": "Find", "sub": f"{n_sites} Seattle sites + month pages",
         "tag": "Tavily", "more": "Searches and reads pages, only from sites we trust. Runs every Monday.", "cost": "~1 search credit per page"},
        {"id": "read", "col": 2, "row": 1, "step": "02", "title": "Read", "sub": "Pages into clean events, in chunks",
         "tag": OPENAI_MODEL, "tagc": "cheap", "img": "steps/s2.png",
         "more": "A low-cost model does the high-volume work: title, date, place, cost, link. Repeats across sites are merged.",
         "cost": f"{m(est['extract']['usd'])} per run · {est['pages']} pages"},
        {"id": "rules", "col": 3, "row": 1, "step": "03", "title": "Rules", "sub": "Free only, no tickets, no real estate",
         "tag": "no model · $0", "tagc": "free", "more": "Cheap, predictable checks run first so a paid model never sees an obvious no."},
        {"id": "judge", "col": 4, "row": 1, "step": "04", "title": "Judge", "sub": "Intent, 0 to 100 score, one-line reason",
         "tag": CURATOR_MODEL, "tagc": "strong", "img": "steps/s3.png",
         "more": "Reads what each event is for, not its keywords. Batches of 20, cached per prompt version."
                 + ("" if CURATOR_MODEL != OPENAI_MODEL else " Set up to swap in a stronger model."),
         "cost": f"{m(est['curate']['usd'])} per run · {est['calls']} calls"},
        {"id": "decide", "col": 5, "row": 1, "step": "05", "title": "Decide", "sub": "The operating point",
         "band": [[f"{hi}+ live", *green], [f"{lo}–{hi - 1} team", *amber], [f"<{lo} out", *red]],
         "more": "Tuned for precision. The middle band goes to people, so borderline events aren't lost."},
        {"id": "publish", "col": 6, "row": 1, "step": "06", "title": "Publish", "sub": "Weekly snapshot for the list",
         "tag": "GitHub Actions · $0", "tagc": "free", "img": "steps/s1.png",
         "more": "Readers load a saved snapshot, so the public page never calls a paid API."},
        {"id": "validate", "col": 2, "row": 2, "lane": "guard", "title": "Validate", "sub": "No date or place? Held, with a reason",
         "tag": "no model", "tagc": "free"},
        {"id": "memory", "col": 4, "row": 2, "lane": "guard", "title": "Memory", "sub": "Latest 12 votes become examples",
         "tag": PROMPT_VERSION, "more": "8 recent downvotes and 4 upvotes are added to the judge's instructions every run."},
        {"id": "breaker", "col": 6, "row": 2, "lane": "guard", "title": "Circuit breaker", "sub": "Holds a run that looks broken",
         "tag": "no model", "tagc": "free",
         "more": "Trips if events halve, most pages fail, sources go quiet, or the AI drops 60%+. Readers keep last week's list."},
        {"id": "evals", "col": 3, "row": 3, "lane": "guard", "title": "Evals", "sub": "Precision and recall vs. our votes",
         "tag": "golden set next", "more": "Every vote is a label. Prompt changes will have to pass a hand-labeled test set."},
        {"id": "team", "col": 5, "row": 3, "lane": "human", "title": "Team review", "sub": "Close calls, thumbs up or down",
         "tag": "people", "tagc": "ppl", "img": "steps/s4.png", "more": "A vote overrides the model right away."},
        {"id": "post", "col": 6, "row": 3, "lane": "human", "title": "Post", "sub": "Our template, then Instagram",
         "tag": "Instagram", "tagc": "ppl", "img": "posts/01-january.jpg" if posts else None,
         "more": "The graphic and caption stay human. That's our voice."},
    ]
    edges = [("find", "read"), ("read", "rules"), ("rules", "judge"), ("judge", "decide"), ("decide", "publish"),
             ("read", "validate"), ("memory", "judge"), ("decide", "team"), ("publish", "breaker"), ("breaker", "post")]
    loops = [("team", "memory", "votes → examples"), ("team", "evals", "votes → labels")]
    components.html(flow.render(nodes, edges, loops), height=flow.HEIGHT)

    examples = [("Free AI Webinar: Grow Your Business 10x", "Sales pitch · 14 · left off", False),
                ("Seattle AI Builders Meetup", "Real meetup · 86 · on the list", True),
                ("Sunday Revival Worship Night", "Religious service · 8 · left off", False),
                ("Diwali Festival of Lights", "Community festival · 92 · on the list", True)]
    st.markdown(howitworks.cost(est) + howitworks.calls(hi, lo, cs_metrics, examples) + howitworks.broke(),
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
        teach_empty(len(labeled))
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


# ---------- navigation ----------
state = st.session_state
state.setdefault("section", "curation")
if state.section not in ("curation", "ontology", "events"):
    state.section = "curation"
if state.get("view") not in [v for v, _ in views]:
    state.view = labels[0]


def go_to(section: str, view: str | None = None) -> None:
    state.section = section
    if view:
        state.view = view


with nav_box:
    st.button("How it works", key="nav-curation", width="stretch", on_click=go_to, args=("curation",),
              type="primary" if state.section == "curation" else "secondary")
    st.button("Ontology of events", key="nav-onto", width="stretch", on_click=go_to, args=("ontology",),
              type="primary" if state.section == "ontology" else "secondary")
    st.button("End result", key="nav-events", width="stretch", on_click=go_to, args=("events",),
              type="primary" if state.section == "events" else "secondary")
    if state.section == "events":
        with st.container(key="nav-months"):
            for v, n in views:
                st.button(f"{v}  ·  {n}", key=f"nav-{v}", width="stretch", on_click=go_to, args=("events", v),
                          type="primary" if state.view == v else "tertiary")

# ---------- page ----------
if state.section == "curation":
    render_curation_page()
elif state.section == "ontology":
    ontology_view.render(ctx)
else:
    render_breaker()
    st.markdown("<div class='ob ob-title'><h1>End result</h1><p>The list we post: free things worth leaving the house for, "
                "picked for outgoing, community-minded Seattleites.</p></div>",
                unsafe_allow_html=True)
    v = state.view
    if v in labels:
        m = months[labels.index(v)]
        render(trace[trace["month"] == (m.year, m.month)], v, v)
    elif v == "Past or undated":
        render(other, "Past, undated, or later", None)
    elif v == "Added by you":
        st.markdown("<div class='ob'><div class='ob-head'><h2>Added by you</h2></div></div>", unsafe_allow_html=True)
        status_by_id = {t["custom_id"]: t for _, t in trace.iterrows() if t["custom"]}
        for e in mine:
            t = status_by_id.get(e["custom_id"])
            a, b = st.columns([6, 1], vertical_alignment="center")
            if t is not None:
                a.markdown(f"<div class='ob ob-list'>{event_row(t['status'], t, held=t['status'] == REVIEW, votes=votes)}</div>",
                           unsafe_allow_html=True)
            if team and b.button("Remove", key=f"rm-{e['custom_id']}", width="stretch"):
                custom_events.remove(e["custom_id"])
                st.rerun()
