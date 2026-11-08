"""Seattle Unlocked event desk: every event pulled, where it came from, and what's live, by month.

    streamlit run app.py
"""
import calendar
import hmac
import html
import os
from collections import Counter
from datetime import date, timedelta
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
import ontology
import snapshot
from agents.reasoner import CATEGORIES
from agents.synthesizer import FILTERED, MERGED, PICK, PUBLISH, REVIEW, SHEET_COLUMNS
from pipeline import build_graph
from tests.sample_events import sample_state
from ui import theme

st.set_page_config(page_title="Seattle Unlocked · Event Desk", layout="wide")

theme.inject()

ICON = ("<svg viewBox='0 0 16 16'><rect x='2' y='3' width='12' height='11' rx='1.5'/>"
        "<path d='M2 6.5h12M5.5 1.5v3M10.5 1.5v3'/></svg>")

CATEGORY_OPTIONS = ["Auto"] + list(CATEGORIES) + ["Community"]


# ---------- data ----------
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


def add_months(d: date, n: int) -> date:
    y, m = divmod(d.month - 1 + n, 12)
    return date(d.year + y, m + 1, 1)


def site(url: str) -> str:
    return urlparse(url).netloc.removeprefix("www.") if str(url).startswith("http") else (url or "unknown")


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
    with st.spinner("Reading listing pages..."):
        try:
            fetched = fetch_live(query)
        except RuntimeError as err:  # missing keys, no credits, and similar setup problems
            st.error(str(err))
            st.stop()
    if not fetched.get("events_raw"):
        st.warning("The circuit breaker held that run, so readers still see the last good list. "
                   "Details are at the top of the Events page.")
    snap, use_sample = snapshot.load(), False
    st.session_state.curate_now = "new"

# Team: score events with the AI curator (new ones, or everything again with the latest votes)
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
                expected = team_password()
                if expected and hmac.compare_digest(pw, expected):
                    st.session_state.team = True
                    st.rerun()
                st.error("That password didn't work." if expected else "Sign in isn't set up yet.")

if is_sample:
    st.markdown("<div class='ob ob-note'>Sample data. These are example events, not live listings.</div>",
                unsafe_allow_html=True)


# ---------- pieces ----------
def esc(x) -> str:
    # "$" is escaped too: Streamlit markdown would otherwise read "$20 ... $50" as math.
    return html.escape(str(x or "")).replace("$", "&#36;")


def day_label(d) -> str:
    return f"{d:%a %b} {d.day}" if isinstance(d, date) and d != date.max else "No date"


def checks_html(t: pd.Series) -> str:
    out = ""
    for c in t["checks"] or []:
        mark = "✓" if c["passed"] else "✕"
        out += f"<span class='chk {'ok' if c['passed'] else 'no'}'>{mark} {esc(c['check'])}</span>"
    fails = [c["detail"] for c in (t["checks"] or []) if not c["passed"]]
    if fails:
        out += f"<span class='chk-why'>{esc(', '.join(fails))}</span>"
    return out


def ai_tag(t) -> str:
    score = t.get("ai_score")
    if score is None or pd.isna(score):
        return ""
    score = int(score)
    level = "hi" if score >= 70 else ("mid" if score >= 40 else "lo")
    vote = votes.get(t.get("key"))
    team_mark = " · team ▲" if vote == 1 else (" · team ▼" if vote == -1 else "")
    return (f"<span class='tag ai {level}' title='{esc(t.get('ai_reason'))}'>AI {score} · "
            f"{esc(t.get('ai_intent'))}{team_mark}</span>")


def event_row(n, t: pd.Series, held: bool = False) -> str:
    title = esc(t["title"]) or "(no title)"
    if t["link"]:
        title = f"<a href='{esc(t['link'])}' target='_blank'>{title}</a>"
    tags = f"<span class='tag cat'>{esc(t['category'])}</span>" if not held and t["category"] else ""
    if t["status"] == PICK:
        tags += "<span class='tag pick'>Pick</span>"
    if t["custom"]:
        tags += "<span class='tag mine'>Added by you</span>"
    tags += ai_tag(t)
    props = [("venue", t["venue"] or "none")]
    if t["neighborhood"]:
        props.append(("area", t["neighborhood"]))
    if t["time"]:
        props.append(("time", t["time"]))
    if t["cost"] != "Free":
        props.append(("cost", t["cost"]))
    props.append(("source", "added by you" if t["custom"] else t["site"]))
    props_html = "".join(f"<span><i>{k}</i>{esc(v)}</span>" for k, v in props)
    if t.get("ai_reason"):
        props_html += f"<span class='ai-why'><i>ai</i>{esc(t['ai_reason'])}</span>"
    extra = f"<div>{checks_html(t)}</div>" if held else ""
    icon_cls = "held" if held else ("mine" if t["custom"] else "")
    right = day_label(t["date"]) if held else ""
    if isinstance(n, str):
        right = esc(n)
    return (f"<div class='ob-row'><div class='ob-ic {icon_cls}'>{ICON}</div><div>"
            f"<div class='ob-t'>{title}{tags}</div><div class='ob-props'>{props_html}</div>{extra}</div>"
            f"<div class='ob-r'>{right}</div></div>")


def sheet_rows(available: pd.DataFrame) -> pd.DataFrame:
    rows = [{
        "title": t["title"], "date": f"{t['date']:%B} {t['date'].day}", "time": t["time"],
        "spot": t["venue"], "hood": t["neighborhood"], "cat": t["category"],
        "desc": t["description"], "cost": t["cost"], "link": t["link"],
        "pick": t["status"] == PICK,
    } for _, t in available.iterrows()]
    return pd.DataFrame(rows, columns=SHEET_COLUMNS)


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
        a.markdown(f"<div class='ob'>{event_row(i, t, held=held)}</div>", unsafe_allow_html=True)
        v = votes.get(t["key"])
        rec = t.to_dict()
        b.button("", icon=":material/thumb_up:", key=f"up-{t['key']}-{t['id']}", help="Feature events like this",
                 type="primary" if v == 1 else "tertiary", on_click=cast_vote, args=(rec, 1))
        c.button("", icon=":material/thumb_down:", key=f"dn-{t['key']}-{t['id']}", help="Don't feature events like this",
                 type="primary" if v == -1 else "tertiary", on_click=cast_vote, args=(rec, -1))


def filtered_row(t: pd.Series) -> str:
    title = esc(t["title"]) or "(no title)"
    if t["link"]:
        title = f"<a href='{esc(t['link'])}' target='_blank'>{title}</a>"
    detail = str(t["why"]).split(": ", 1)[-1]
    props = [("date", day_label(t["date"])), ("venue", t["venue"] or "none"), ("cost", t["cost"]),
             ("source", t["site"])]
    props_html = "".join(f"<span><i>{k}</i>{esc(v)}</span>" for k, v in props)
    return (f"<div class='ob-row'><div class='ob-ic held'>{ICON}</div><div>"
            f"<div class='ob-t'>{title}</div><div class='ob-props'>{props_html}</div>"
            f"<div><span class='chk no'>matched: {esc(detail)}</span></div></div>"
            f"<div class='ob-r'></div></div>")


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
            rows += event_row(n, t)
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
    rows = "".join(event_row(i, t, held=True) for i, (_, t) in enumerate(held.iterrows(), 1)) \
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
@st.cache_resource
def vis_js() -> str:
    """The vis-network library, bundled in assets/ so the graph never depends on a CDN."""
    from pathlib import Path
    return (Path(__file__).parent / "assets" / "vis-network.min.js").read_text()


TYPE_COLOR = {"Category": "#A04D74", "Neighborhood": "#5E8C7A", "Source": "#D29A3A", "Venue": "#B9AFBF"}


def graph_html(graph: dict, show_venues: bool, live_only: bool) -> str:
    """An interactive network of categories, neighborhoods, sources (and venues)."""
    nodes = {n["id"]: n for n in graph["nodes"]}
    weight = "live" if live_only else "events"
    keep_types = {"Category", "Neighborhood", "Source"} | ({"Venue"} if show_venues else set())
    # Roll event-level edges up into thing-to-thing links, weighted by events in common.
    ev_links: dict[str, dict[str, list]] = {}
    for e in graph["edges"]:
        src = nodes.get(e["source"])
        if src and src["type"] == "Event" and (src["live"] or not live_only):
            ev_links.setdefault(e["source"], {}).setdefault(e["rel"], []).append(e["target"])
    pair = Counter()
    for links in ev_links.values():
        cat = (links.get("IS_A") or [None])[0]
        hood = (links.get("IN_AREA") or [None])[0]
        srcn = (links.get("FOUND_ON") or [None])[0]
        venue = (links.get("HAPPENS_AT") or [None])[0]
        if cat and hood:
            pair[(cat, hood)] += 1
        if srcn and cat:
            pair[(srcn, cat)] += 1
        if show_venues and venue and hood:
            pair[(venue, hood)] += 1
    used = {a for a, _ in pair} | {b for _, b in pair}
    # Keep the graph readable: top neighborhoods and venues only.
    def top(kind, k):
        cand = [n for n in nodes.values() if n["type"] == kind and n["id"] in used and n[weight] > 0]
        return {n["id"] for n in sorted(cand, key=lambda n: -n[weight])[:k]}
    allowed = ({n["id"] for n in nodes.values() if n["type"] in ("Category", "Source") and n[weight] > 0}
               | top("Neighborhood", 22) | (top("Venue", 25) if show_venues else set()))
    vis_nodes = [{"id": nid, "label": nodes[nid]["label"], "group": nodes[nid]["type"],
                  "value": max(nodes[nid][weight], 1),
                  "title": f"{nodes[nid]['type']} · {nodes[nid][weight]} events",
                  "color": TYPE_COLOR[nodes[nid]["type"]]}
                 for nid in allowed if nodes[nid]["type"] in keep_types]
    ids = {n["id"] for n in vis_nodes}
    vis_edges = [{"from": a, "to": b, "value": k, "title": f"{k} events"}
                 for (a, b), k in pair.items() if a in ids and b in ids]
    import json as _json
    return """
<div id="net" style="width:100%;height:560px;background:#FFFFFF;border:1px solid #ECE6E1;border-radius:12px"></div>
<div style="font:13px Figtree,sans-serif;color:#6E6676;margin-top:8px;display:flex;gap:16px">
  <span><b style="color:#A04D74">●</b> Category</span><span><b style="color:#5E8C7A">●</b> Neighborhood</span>
  <span><b style="color:#D29A3A">●</b> Source</span>""" + (
        '<span><b style="color:#B9AFBF">●</b> Venue</span>' if show_venues else "") + """
</div>
<script>VISJS</script>
<script>
const data = {nodes: new vis.DataSet(NODES), edges: new vis.DataSet(EDGES)};
const net = new vis.Network(document.getElementById('net'), data, {
  nodes: {shape: 'dot', scaling: {min: 6, max: 34, label: {enabled: true, min: 11, max: 18}},
          font: {color: '#2A2433', face: 'Figtree, sans-serif', strokeWidth: 4, strokeColor: '#FFFFFF'},
          borderWidth: 0},
  edges: {color: {color: 'rgba(110,102,118,0.18)', highlight: '#A04D74'}, scaling: {min: 1, max: 7},
          smooth: {type: 'continuous'}},
  physics: {barnesHut: {gravitationalConstant: -6000, springLength: 120, centralGravity: 0.35},
            stabilization: {iterations: 400}},
  interaction: {hover: true, tooltipDelay: 120}
});
const refit = () => { net.setSize('100%', '560px'); net.redraw(); net.fit({animation: false}); };
net.once('stabilizationIterationsDone', () => { net.setOptions({physics: false}); refit(); });
window.addEventListener('resize', refit);
setTimeout(refit, 600); setTimeout(refit, 1800);
</script>""".replace("NODES", _json.dumps(vis_nodes)).replace("EDGES", _json.dumps(vis_edges)).replace("VISJS", vis_js())


def render_ontology(trace_rows: list[dict], month_labels: list[str]) -> None:
    st.markdown(
        "<div class='ob'><div class='ob-head'><h2>Graph</h2>"
        f"<span class='ob-type'>{len(trace_rows)} events</span></div></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([2, 2, 1])
    month = c1.selectbox("Month", ["All months"] + month_labels, key="onto-month")
    scope = c2.radio("Events", ["Free and live", "Everything pulled"], horizontal=True, key="onto-scope")
    show_venues = c3.toggle("Venues", key="onto-venues")
    rows = [t for t in trace_rows if month == "All months"
            or (isinstance(t.get("date"), date) and f"{t['date']:%B %Y}" == month)]
    graph = ontology.build(rows)
    sm = ontology.summary(graph)
    live_only = scope == "Free and live"
    counts = Counter(n["type"] for n in graph["nodes"] if n["live"] or not live_only)
    live_events = {n["id"] for n in graph["nodes"] if n["type"] == "Event" and (n["live"] or not live_only)}
    n_links = sum(1 for e in graph["edges"] if e["source"] in live_events)

    stats = [("Events", counts["Event"]), ("Categories", counts["Category"]), ("Venues", counts["Venue"]),
             ("Neighborhoods", counts["Neighborhood"]), ("Sources", counts["Source"]),
             ("Links", n_links)]
    st.markdown("<div class='ob'><div class='ob-stats'>" + "".join(
        f"<div class='ob-stat'><span>{k}</span><b>{v}</b></div>" for k, v in stats) + "</div></div>",
        unsafe_allow_html=True)
    st.write("")
    components.html(graph_html(graph, show_venues, live_only), height=600)

    hood_cat = sm["hood_cat"] if live_only else Counter(
        (r["neighborhood"], r["category"]) for r in sm["rows"] if r["neighborhood"] and r["status"] != MERGED)

    a, b = st.columns(2, gap="large")
    with a:
        st.markdown("<div class='ob ob-sec'><span class='dot'></span><span class='t'>Where free events happen</span>"
                    "</div>" if live_only else "<div class='ob ob-sec'><span class='dot'></span>"
                    "<span class='t'>Where events happen</span></div>", unsafe_allow_html=True)
        if hood_cat:
            df = pd.Series(hood_cat).unstack(fill_value=0)
            df = df.loc[df.sum(axis=1).sort_values(ascending=False).index[:12]]
            df = df[df.sum().sort_values(ascending=False).index[:7]]
            top_v = max(int(df.values.max()), 1)
            heat = lambda v: (f"background-color: rgba(160,77,116,{0.08 + 0.6 * v / top_v:.2f}); "
                              f"color: {'#FFFFFF' if v / top_v > .55 else '#2A2433'}" if v else "color: #706877")
            st.dataframe(df.style.map(heat), width="stretch")
    with b:
        st.markdown("<div class='ob ob-sec'><span class='dot'></span><span class='t'>Repeat venues</span>"
                    "<span class='c'>partnership leads</span></div>", unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(sm["repeat_venues"][:15], columns=["Venue", "Neighborhood", "Free events"]),
                     hide_index=True, width="stretch")

    a, b = st.columns(2, gap="large")
    with a:
        st.markdown("<div class='ob ob-sec rec'><span class='dot'></span><span class='t'>Sources</span></div>",
                    unsafe_allow_html=True)
        src = pd.DataFrame([{"Source": k, "Found": v["found"], "Free and live": v["live"],
                             "Only here": v["unique"], "Repeats": v["repeats"], "Paid": v["paid"]}
                            for k, v in sm["sources"].items()]).sort_values("Found", ascending=False)
        st.dataframe(src, hide_index=True, width="stretch")
    with b:
        st.markdown("<div class='ob ob-sec held'><span class='dot'></span><span class='t'>Free vs paid by category"
                    "</span></div>", unsafe_allow_html=True)
        cat = pd.DataFrame([{"Category": k, "Free": v["free"], "Paid": v["paid"], "Held": v["held"]}
                            for k, v in sm["categories"].items()])
        if not cat.empty:
            cat["Free share"] = (cat["Free"] / (cat["Free"] + cat["Paid"]).replace(0, pd.NA)).map(
                lambda x: "" if pd.isna(x) else f"{x:.0%}")
            st.dataframe(cat.sort_values("Free", ascending=False), hide_index=True, width="stretch")


# ---------- AI curation page ----------
def venn_svg() -> str:
    """What makes a pick: free, community, and adventure. The pick is where all three meet."""
    t = "fill:var(--text)"
    d = "fill:var(--dim)"
    return f"""
<svg viewBox="0 0 580 440" role="img" aria-label="Venn diagram: free, community, and adventure overlap in the pick">
  <circle cx="210" cy="160" r="135" style="fill:#6C7FD1;fill-opacity:.14;stroke:#6C7FD1;stroke-width:1.5"/>
  <circle cx="370" cy="160" r="135" style="fill:#7FAED8;fill-opacity:.16;stroke:#5F8FBF;stroke-width:1.5"/>
  <circle cx="290" cy="290" r="135" style="fill:#E3A6C0;fill-opacity:.2;stroke:#C77F9F;stroke-width:1.5"/>
  <g font-family="Figtree,sans-serif" text-anchor="middle">
    <text x="150" y="120" font-size="17" font-weight="700" style="fill:#4F5FB0">Community</text>
    <text x="150" y="140" font-size="13" style="{d}">brings people</text>
    <text x="150" y="156" font-size="13" style="{d}">together</text>
    <text x="430" y="120" font-size="17" font-weight="700" style="fill:#3F6E9C">Free</text>
    <text x="430" y="140" font-size="13" style="{d}">no cost, no</text>
    <text x="430" y="156" font-size="13" style="{d}">upsell</text>
    <text x="290" y="372" font-size="17" font-weight="700" style="fill:#A65A7D">Adventure</text>
    <text x="290" y="392" font-size="13" style="{d}">new places, outdoors,</text>
    <text x="290" y="408" font-size="13" style="{d}">first-time things</text>
    <text x="290" y="100" font-size="13" style="{t}">Potlucks</text>
    <text x="290" y="117" font-size="13" style="{t}">Cleanups</text>
    <text x="203" y="252" font-size="13" style="{t}">Festivals</text>
    <text x="203" y="269" font-size="13" style="{t}">Art walks</text>
    <text x="377" y="252" font-size="13" style="{t}">Trail days</text>
    <text x="377" y="269" font-size="13" style="{t}">Free classes</text>
    <text x="290" y="200" font-size="18" font-weight="700" style="{t}">The pick</text>
    <text x="290" y="218" font-size="12" style="{d}">all three</text>
  </g>
</svg>"""


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
labels = [f"{m:%B %Y}" for m in months]
in_range = {(m.year, m.month) for m in months}
other = trace[~trace["month"].isin(in_range)]
views = [(lab, int((trace["month"] == (m.year, m.month)).sum())) for lab, m in zip(labels, months)]
if not other.empty:
    views.append(("Past or undated", len(other)))
if mine:
    views.append(("Added by you", len(mine)))

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
    st.markdown("<div class='ob ob-title'><h1>Ontology of events</h1>"
                "<p>How Seattle's free events connect: categories, neighborhoods, venues, and sources.</p></div>",
                unsafe_allow_html=True)
    render_ontology(res["trace"], labels)
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
                a.markdown(f"<div class='ob ob-list'>{event_row(t['status'], t, held=t['status'] == REVIEW)}</div>",
                           unsafe_allow_html=True)
            if team and b.button("Remove", key=f"rm-{e['custom_id']}", width="stretch"):
                custom_events.remove(e["custom_id"])
                st.rerun()
