"""Seattle Unlocked event desk: every event pulled, where it came from, and what's live, by month.

    streamlit run app.py
"""
import calendar
import hmac
import html
import os
from collections import Counter
from datetime import date
from urllib.parse import urlparse

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

import custom_events
import ontology
import snapshot
from agents.reasoner import CATEGORIES
from agents.synthesizer import FILTERED, MERGED, PICK, PUBLISH, REVIEW, SHEET_COLUMNS
from pipeline import build_graph
from tests.sample_events import sample_state

st.set_page_config(page_title="Seattle Unlocked · Event Desk", layout="wide")

# Look: a dark, dense object explorer. Each event is an object with properties.
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');
:root{--bg:#1C2127;--panel:#252A31;--panel2:#2F343C;--line:#383E47;--line2:#404854;
      --text:#F6F7F9;--dim:#ABB3BF;--muted:#738091;--blue:#4C90F0;--blue-bg:rgba(45,114,210,.2);
      --green:#72CA9B;--green-bg:rgba(35,133,81,.25);--red:#FA999C;--red-bg:rgba(205,66,70,.25);
      --orange:#F0B726;--mono:'JetBrains Mono',Menlo,monospace}
html, body, .stApp, .stMarkdown p, label, input, textarea, button p {font-family:'Inter',-apple-system,'Segoe UI',sans-serif}
.block-container{padding-top:3.2rem;max-width:1240px}
.ob, .ob *, .stTabs [data-baseweb="tab"] p, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label{font-family:'Inter',-apple-system,'Segoe UI',sans-serif !important}
[data-testid="stSidebar"]{background:#111418;border-right:1px solid var(--line)}
[data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span{color:var(--dim)}
[data-testid="stSidebar"] button[kind="primary"]{background:#2D72D2;border-color:#2D72D2;border-radius:3px}
[data-testid="stSidebar"] button[kind="primary"] p{color:#fff;font-weight:600}
[data-testid="stSidebar"] button[kind="secondary"]{background:var(--panel2);border:1px solid var(--line2);border-radius:3px}
[data-testid="stSidebar"] button[kind="secondary"] p{color:var(--text)}
.stTabs [data-baseweb="tab-list"]{gap:2px;border-bottom:1px solid var(--line)}
.stTabs [data-baseweb="tab"]{padding:6px 12px}
.stTabs [data-baseweb="tab"] p{font-size:13px;font-weight:500;color:var(--dim)}
.stTabs [aria-selected="true"] p{color:var(--text)}
.ob-brand{font-size:13px;font-weight:600;color:var(--text);display:flex;align-items:center;gap:8px}
.ob-brand i{display:inline-block;width:18px;height:18px;border-radius:3px;background:#2D72D2}
.ob-crumb{font-family:var(--mono) !important;font-size:12px;color:var(--muted);margin-top:10px}
.ob-crumb b{color:var(--dim);font-weight:500}
.ob-head{display:flex;align-items:center;gap:12px;margin:6px 0 16px}
.ob-head h2{font-size:24px;font-weight:600;color:var(--text);margin:0;padding:0}
.ob-type{font-family:var(--mono) !important;font-size:11px;color:var(--blue);background:var(--blue-bg);padding:2px 8px;border-radius:3px}
.ob-stats{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:8px}
.ob-stat{background:var(--panel);border:1px solid var(--line);border-radius:3px;padding:10px 12px}
.ob-stat span{display:block;font-size:11px;font-weight:500;letter-spacing:.04em;text-transform:uppercase;color:var(--muted)}
.ob-stat b{display:block;font-size:22px;font-weight:600;color:var(--text);margin-top:2px;font-variant-numeric:tabular-nums}
.ob-stat.blue b{color:var(--blue)}.ob-stat.red b{color:var(--red)}.ob-stat.green b{color:var(--green)}
.ob-sec{display:flex;align-items:center;gap:8px;margin:26px 0 0;padding:9px 12px;background:var(--panel);
        border:1px solid var(--line);border-bottom:none;border-radius:3px 3px 0 0}
.ob-sec .t{font-size:13px;font-weight:600;color:var(--text)}
.ob-sec .c{font-family:var(--mono) !important;font-size:11px;color:var(--dim);background:var(--panel2);padding:1px 7px;border-radius:9px}
.ob-sec .dot{width:8px;height:8px;border-radius:50%;background:var(--green)}
.ob-sec.held .dot{background:var(--red)}.ob-sec.rec .dot{background:var(--blue)}
.ob-list{border:1px solid var(--line);border-radius:0 0 3px 3px;background:#20252B}
.ob-day{font-family:var(--mono) !important;font-size:11px;color:var(--muted);padding:8px 12px;background:#1E2329;
        border-top:1px solid var(--line)}
.ob-day:first-child{border-top:none}
.ob-row{display:grid;grid-template-columns:28px minmax(0,1fr) auto;gap:12px;align-items:start;padding:10px 12px;
        border-top:1px solid var(--line)}
.ob-row:hover{background:var(--panel)}
.ob-ic{width:28px;height:28px;border-radius:3px;background:var(--blue-bg);display:grid;place-items:center}
.ob-ic svg{width:15px;height:15px;fill:none;stroke:var(--blue);stroke-width:1.6}
.ob-ic.mine{background:var(--green-bg)}.ob-ic.mine svg{stroke:var(--green)}
.ob-ic.held{background:var(--red-bg)}.ob-ic.held svg{stroke:var(--red)}
.ob-t{font-size:14px;font-weight:600;color:var(--text);line-height:1.4}
.ob-t a{color:var(--text);text-decoration:none}.ob-t a:hover{color:var(--blue);text-decoration:underline}
.ob-props{display:flex;flex-wrap:wrap;gap:4px 16px;margin-top:3px;font-size:12px;color:var(--dim)}
.ob-props i{font-style:normal;font-family:var(--mono) !important;font-size:11px;color:var(--muted);margin-right:5px}
.ob-r{font-family:var(--mono) !important;font-size:12px;color:var(--dim);white-space:nowrap;padding-top:2px}
.tag{display:inline-block;font-size:11px;font-weight:500;padding:1px 7px;margin-left:8px;border-radius:3px;vertical-align:1px}
.tag.cat{background:rgba(143,153,168,.18);color:var(--dim)}
.tag.pick{background:var(--blue-bg);color:#8ABBFF}
.tag.mine{background:var(--green-bg);color:var(--green)}
.chk{display:inline-block;font-family:var(--mono) !important;font-size:11px;padding:1px 7px;margin:6px 4px 0 0;border-radius:3px}
.chk.ok{background:var(--green-bg);color:var(--green)}
.chk.no{background:var(--red-bg);color:var(--red)}
.chk-why{font-size:12px;color:var(--red);margin-left:6px}
.src-chips{display:flex;flex-wrap:wrap;gap:6px;padding:10px 12px;border:1px solid var(--line);border-top:none;background:#20252B}
.src-chips span{font-family:var(--mono) !important;font-size:11px;background:var(--panel2);border:1px solid var(--line2);
                padding:2px 8px;border-radius:3px;color:var(--dim)}
.src-chips b{color:var(--text);font-weight:500;margin-left:6px}
.empty{color:var(--muted);font-size:13px;padding:14px 12px;border:1px solid var(--line);border-top:none;background:#20252B}
.ob-title{padding:6px 0 18px;margin-bottom:18px;border-bottom:1px solid var(--line)}
.ob-title h1{font-size:40px;font-weight:600;letter-spacing:-.02em;color:var(--text);margin:0;padding:0;line-height:1.1}
.ob-title p{font-size:15px;color:var(--dim);margin:6px 0 0}
.st-key-nav{margin-top:14px}
.st-key-nav button{justify-content:flex-start;border-radius:3px;min-height:36px;padding-left:12px}
.st-key-nav button > div, .st-key-nav button [data-testid="stMarkdownContainer"]{justify-content:flex-start;text-align:left;width:100%}
.st-key-nav button p{font-size:14px;font-weight:600}
.st-key-nav-months{padding-left:14px;border-left:1px solid var(--line2);margin:2px 0 6px 10px}
.st-key-nav-months button{min-height:30px}
.st-key-nav-months button p{font-size:13px;font-weight:500;color:var(--dim)}
.st-key-nav-months button[kind="primary"] p{color:#fff}
.st-key-nav-months [data-testid="stVerticalBlock"]{gap:2px}
.ob-note{font-size:12px;color:var(--orange);background:rgba(240,183,38,.12);border:1px solid rgba(240,183,38,.3);
         border-radius:3px;padding:6px 10px;margin-bottom:10px;display:inline-block}
@media (max-width:900px){.ob-stats{grid-template-columns:repeat(2,minmax(0,1fr))}}
</style>
""", unsafe_allow_html=True)

ICON = ("<svg viewBox='0 0 16 16'><rect x='2' y='3' width='12' height='11' rx='1.5'/>"
        "<path d='M2 6.5h12M5.5 1.5v3M10.5 1.5v3'/></svg>")

CATEGORY_OPTIONS = ["Auto"] + list(CATEGORIES) + ["Community"]


# ---------- data ----------
def fetch_live(query: str) -> dict:
    """Steps 1 to 2: the slow, paid part. Team only, and it saves a new snapshot."""
    raw = build_graph(stop_after="extractor").invoke({"query": query})
    if raw.get("events_raw"):
        snapshot.save(raw)
    return raw


def team_password() -> str:
    try:
        return str(st.secrets.get("TEAM_PASSWORD", "")) or os.getenv("TEAM_PASSWORD", "")
    except Exception:  # no secrets file locally
        return os.getenv("TEAM_PASSWORD", "")


def finish(raw: dict, custom: list[dict], end: date, picks: int, include_paid: bool) -> dict:
    """Steps 3 to 6: fast, so they rerun whenever settings or your events change."""
    state = {**raw, "custom_events": custom, "window_end": end,
             "max_picks": picks, "free_only": not include_paid}
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
        st.warning("That run found no events, so the last snapshot is still showing.")
    snap, use_sample = snapshot.load(), False

if use_sample or snap is None:
    raw, as_of, is_sample = sample_state(), None, True
else:
    raw, as_of, is_sample = snap, snapshot.fetched_on(snap), False

today = raw.get("today") if is_sample else date.today()
months = [add_months(today.replace(day=1), i) for i in range(n_months)]
last = months[-1]
end = last.replace(day=calendar.monthrange(last.year, last.month)[1])

mine = custom_events.load()
res = finish(raw, mine, end, picks, include_paid)
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
    return html.escape(str(x or ""))


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


def event_row(n, t: pd.Series, held: bool = False) -> str:
    title = esc(t["title"]) or "(no title)"
    if t["link"]:
        title = f"<a href='{esc(t['link'])}' target='_blank'>{title}</a>"
    tags = f"<span class='tag cat'>{esc(t['category'])}</span>" if not held and t["category"] else ""
    if t["status"] == PICK:
        tags += "<span class='tag pick'>Pick</span>"
    if t["custom"]:
        tags += "<span class='tag mine'>Added by you</span>"
    props = [("venue", t["venue"] or "none")]
    if t["neighborhood"]:
        props.append(("area", t["neighborhood"]))
    if t["time"]:
        props.append(("time", t["time"]))
    if t["cost"] != "Free":
        props.append(("cost", t["cost"]))
    props.append(("source", "added by you" if t["custom"] else t["site"]))
    props_html = "".join(f"<span><i>{k}</i>{esc(v)}</span>" for k, v in props)
    extra = f"<div>{checks_html(t)}</div>" if held else ""
    icon_cls = "held" if held else ("mine" if t["custom"] else "")
    right = day_label(t["date"]) if held else esc(t["id"])
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
    color = {"✓": "color:#72CA9B;font-weight:600", "✕": "color:#FA999C;font-weight:600"}
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


def render(df: pd.DataFrame, label: str, file_label: str | None) -> None:
    order = {PICK: 0, PUBLISH: 0, REVIEW: 1, MERGED: 2, FILTERED: 3}
    df = df.assign(_o=df["status"].map(order),
                   _d=df["date"].map(lambda d: d if isinstance(d, date) else date.max))
    df = df.sort_values(["_o", "_d", "title"])
    available = df[df["status"].isin([PICK, PUBLISH])]
    held = df[df["status"] == REVIEW]
    c = Counter(df["status"])
    sources = Counter(df.loc[df["status"] != MERGED, "site"])

    st.markdown(
        f"<div class='ob'>"
        f"<div class='ob-head'><h2>{esc(label)}</h2><span class='ob-type'>{len(df)} objects</span></div>"
        f"<div class='ob-stats'>"
        f"<div class='ob-stat green'><span>Available</span><b>{len(available)}</b></div>"
        f"<div class='ob-stat blue'><span>Picks</span><b>{c[PICK]}</b></div>"
        f"<div class='ob-stat red'><span>Held</span><b>{c[REVIEW]}</b></div>"
        f"<div class='ob-stat'><span>Duplicates</span><b>{c[MERGED]}</b></div>"
        f"<div class='ob-stat'><span>Filtered</span><b>{c[FILTERED]}</b></div>"
        f"<div class='ob-stat'><span>Sources</span><b>{len(sources)}</b></div>"
        f"</div></div>", unsafe_allow_html=True)

    # 1. Available
    st.markdown(f"<div class='ob ob-sec'><span class='dot'></span><span class='t'>Available</span>"
                f"<span class='c'>{len(available)}</span></div>", unsafe_allow_html=True)
    if available.empty:
        st.markdown("<div class='ob empty'>No events ready for this month yet.</div>", unsafe_allow_html=True)
    body, n = "", 0
    for d, group in available.groupby("_d", sort=True):
        body += f"<div class='ob-day'>{day_label(d)} · {len(group)}</div>"
        for _, t in group.iterrows():
            n += 1
            body += event_row(n, t)
    if body:
        st.markdown(f"<div class='ob ob-list'>{body}</div>", unsafe_allow_html=True)

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

    # 2. Held
    st.markdown(f"<div class='ob ob-sec held'><span class='dot'></span><span class='t'>Held for review</span>"
                f"<span class='c'>{len(held)}</span></div>", unsafe_allow_html=True)
    if held.empty:
        st.markdown("<div class='ob empty'>Nothing held.</div>", unsafe_allow_html=True)
    else:
        rows = "".join(event_row(i, t, held=True) for i, (_, t) in enumerate(held.iterrows(), 1))
        st.markdown(f"<div class='ob ob-list'>{rows}</div>", unsafe_allow_html=True)

    # 3. Full record
    st.markdown(f"<div class='ob ob-sec rec'><span class='dot'></span><span class='t'>Full record</span>"
                f"<span class='c'>{len(df)}</span></div>", unsafe_allow_html=True)
    st.markdown("<div class='ob src-chips'>" + "".join(
        f"<span>{esc(s)}<b>{k}</b></span>" for s, k in sources.most_common()) + "</div>",
        unsafe_allow_html=True)
    st.write("")
    record_table(df, key=f"rec-{label}")


# ---------- ontology ----------
@st.cache_resource
def vis_js() -> str:
    """The vis-network library, bundled in assets/ so the graph never depends on a CDN."""
    from pathlib import Path
    return (Path(__file__).parent / "assets" / "vis-network.min.js").read_text()


TYPE_COLOR = {"Category": "#4C90F0", "Neighborhood": "#72CA9B", "Source": "#F0B726", "Venue": "#ABB3BF"}


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
<div id="net" style="width:100%;height:560px;background:#1C2127;border:1px solid #383E47;border-radius:3px"></div>
<div style="font:12px Inter,sans-serif;color:#ABB3BF;margin-top:8px;display:flex;gap:16px">
  <span><b style="color:#4C90F0">●</b> Category</span><span><b style="color:#72CA9B">●</b> Neighborhood</span>
  <span><b style="color:#F0B726">●</b> Source</span>""" + (
        '<span><b style="color:#ABB3BF">●</b> Venue</span>' if show_venues else "") + """
</div>
<script>VISJS</script>
<script>
const data = {nodes: new vis.DataSet(NODES), edges: new vis.DataSet(EDGES)};
const net = new vis.Network(document.getElementById('net'), data, {
  nodes: {shape: 'dot', scaling: {min: 6, max: 34, label: {enabled: true, min: 11, max: 18}},
          font: {color: '#F6F7F9', face: 'Inter, sans-serif', strokeWidth: 3, strokeColor: '#1C2127'},
          borderWidth: 0},
  edges: {color: {color: 'rgba(171,179,191,0.22)', highlight: '#4C90F0'}, scaling: {min: 1, max: 7},
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
            heat = lambda v: (f"background-color: rgba(76,144,240,{0.12 + 0.75 * v / top_v:.2f}); color: #F6F7F9"
                              if v else "color: #5C6370")
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
state.setdefault("section", "events")
if state.get("view") not in [v for v, _ in views]:
    state.view = labels[0]


def go_to(section: str, view: str | None = None) -> None:
    state.section = section
    if view:
        state.view = view


with nav_box:
    st.button("Events", key="nav-events", width="stretch", on_click=go_to, args=("events",),
              type="primary" if state.section == "events" else "secondary")
    if state.section == "events":
        with st.container(key="nav-months"):
            for v, n in views:
                st.button(f"{v}  ·  {n}", key=f"nav-{v}", width="stretch", on_click=go_to, args=("events", v),
                          type="primary" if state.view == v else "tertiary")
    st.button("Ontology of events", key="nav-onto", width="stretch", on_click=go_to, args=("ontology",),
              type="primary" if state.section == "ontology" else "secondary")

# ---------- page ----------
if state.section == "ontology":
    st.markdown("<div class='ob ob-title'><h1>Ontology of events</h1>"
                "<p>How Seattle's free events connect: categories, neighborhoods, venues, and sources.</p></div>",
                unsafe_allow_html=True)
    render_ontology(res["trace"], labels)
else:
    st.markdown("<div class='ob ob-title'><h1>Seattle Free Events</h1><p>Curated list</p></div>",
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
