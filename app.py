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
import illustrations
import filters
from agents.curator import AUDIENCE, INTENTS, LOW_VALUE, PROMPT_VERSION, build_messages
from crm import view as crm_view
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
@import url('https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700&family=Fredoka:wght@500;600&display=swap');
/* Look: light and quiet like Stripe, warmer and softer. Warm white, plum accent, sage for good, coral for held. */
:root{--bg:#FBF9F7;--panel:#FFFFFF;--panel2:#F6F2EF;--line:#ECE6E1;--line2:#E2DAD4;
      --text:#2A2433;--dim:#6E6676;--muted:#706877;
      --blue:#A04D74;--blue-bg:rgba(160,77,116,.09);
      --green:#456F5E;--green-bg:rgba(94,140,122,.12);
      --red:#B14A40;--red-bg:rgba(194,86,75,.09);
      --orange:#8F6214;--mono:'Figtree',-apple-system,'Segoe UI',sans-serif;
      --shadow:0 1px 2px rgba(42,36,51,.04),0 2px 8px rgba(42,36,51,.04)}
html, body, .stApp, .stMarkdown p, label, input, textarea, button p {font-family:'Figtree',-apple-system,'Segoe UI',sans-serif}
.stApp{background:var(--bg)}
.block-container{padding-top:3.4rem;max-width:1160px}
.ob, .ob *, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label{font-family:'Figtree',-apple-system,'Segoe UI',sans-serif !important}

/* sidebar */
[data-testid="stSidebar"]{background:#F6F2EF;border-right:1px solid var(--line)}
[data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span{color:var(--dim)}
[data-testid="stSidebar"] button{border-radius:8px;box-shadow:none}
[data-testid="stSidebar"] button[kind="primary"]{background:var(--blue);border-color:var(--blue)}
[data-testid="stSidebar"] button[kind="primary"] p{color:#fff;font-weight:600}
[data-testid="stSidebar"] button[kind="secondary"]{background:#fff;border:1px solid var(--line2)}
[data-testid="stSidebar"] button[kind="secondary"] p{color:var(--text)}
.ob-brand{font-size:15px;font-weight:700;color:var(--text);display:flex;align-items:center;gap:9px;letter-spacing:-.01em}
.ob-brand i{display:inline-block;width:20px;height:20px;border-radius:50%;
            background:radial-gradient(circle at 35% 35%,#E7B3C8,#A04D74)}
.st-key-nav{margin-top:18px}
.st-key-nav button{justify-content:flex-start;min-height:36px;padding-left:12px;border:none !important;background:transparent !important}
.st-key-nav button > div, .st-key-nav button [data-testid="stMarkdownContainer"]{justify-content:flex-start;text-align:left;width:100%}
.st-key-nav button p{font-size:15px;font-weight:500;color:var(--text) !important}
.st-key-nav button:hover{background:rgba(42,36,51,.05) !important}
.st-key-nav button[kind="primary"]{background:var(--blue-bg) !important}
.st-key-nav button[kind="primary"] p{color:var(--blue) !important;font-weight:600}
.st-key-nav-months{padding-left:12px;border-left:1px solid var(--line2);margin:2px 0 6px 14px}
.st-key-nav-months button{min-height:30px}
.st-key-nav-months button p{font-size:14px !important;font-weight:400 !important;color:var(--dim) !important}
.st-key-nav-months button[kind="primary"] p{color:var(--blue) !important;font-weight:600 !important}
.st-key-nav-months [data-testid="stVerticalBlock"]{gap:2px}

/* page title */
.ob-title{padding:4px 0 22px;margin-bottom:22px;border-bottom:1px solid var(--line)}
.ob-title h1{font-size:38px;font-weight:700;letter-spacing:-.025em;color:var(--text);margin:0;padding:0;line-height:1.1}
.ob-title p{font-size:16px;color:var(--dim);margin:8px 0 0;max-width:62ch;line-height:1.5}
.ob-head{display:flex;align-items:baseline;gap:12px;margin:4px 0 16px}
.ob-head h2{font-size:24px;font-weight:700;letter-spacing:-.015em;color:var(--text);margin:0;padding:0}
.ob-type{font-size:13px;color:var(--muted)}
.ob-crumb{font-size:13px;color:var(--muted)}

/* stat cards */
.ob-stats{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:12px}
.ob-stat{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px;box-shadow:var(--shadow)}
.ob-stat span{display:block;font-size:13px;font-weight:500;color:var(--dim)}
.ob-stat b{display:block;font-size:26px;font-weight:700;letter-spacing:-.02em;color:var(--text);margin-top:4px;font-variant-numeric:tabular-nums}
.ob-stat.blue b{color:var(--blue)}.ob-stat.red b{color:var(--red)}.ob-stat.green b{color:var(--green)}
a.ob-stat.link{text-decoration:none;display:block;cursor:pointer}
a.ob-stat.link:hover{border-color:var(--orange)}
a.ob-stat.link b{color:var(--orange)}

/* sections: a plain heading, then a white card */
.ob-sec{display:flex;align-items:baseline;gap:8px;margin:34px 0 10px;padding:0;background:none;border:none}
.ob-sec .t{font-size:18px;font-weight:700;letter-spacing:-.01em;color:var(--text)}
.ob-sec .c{font-size:14px;color:var(--muted)}
.ob-sec .dot{display:none}
.ob-sec .hint{margin-left:auto;font-size:13px;color:var(--muted);font-weight:400}
.ob-list{border:1px solid var(--line);border-radius:12px;background:var(--panel);box-shadow:var(--shadow);overflow:hidden}
.ob-acc{margin-top:0}
.ob-acc > summary{list-style:none;cursor:pointer;user-select:none}
.ob-acc > summary::-webkit-details-marker, .ob-acc-day > summary::-webkit-details-marker{display:none}
.ob-acc-day > summary{list-style:none;cursor:pointer;user-select:none}
.ob-acc-day > summary:hover{background:#F8F4F1}
.chev{display:inline-block;width:0;height:0;border-left:5px solid var(--muted);border-top:4px solid transparent;
      border-bottom:4px solid transparent;margin-right:4px;transition:transform .15s}
details[open] > summary .chev{transform:rotate(90deg)}
.ob-empty-in{color:var(--muted);font-size:14px;padding:16px}
.empty{color:var(--dim);font-size:14px;padding:16px;border:1px solid var(--line);border-radius:12px;background:var(--panel)}

/* day headers */
.ob-day{display:flex;align-items:center;gap:10px;font-size:16px;font-weight:600;color:var(--text);
        padding:12px 16px;background:#FCFAF8;border-top:1px solid var(--line)}
.ob-acc-day:first-child .ob-day{border-top:none}
.ob-day .wd{font-size:13px;font-weight:600;color:var(--blue);background:var(--blue-bg);padding:2px 9px;border-radius:999px}
.ob-day .n{margin-left:auto;font-size:13px;font-weight:400;color:var(--muted)}
.ob-day.weekend .wd{color:var(--green);background:var(--green-bg)}
.ob-day.filt .wd{color:var(--orange);background:rgba(176,122,34,.1)}

/* event rows */
.ob-row{display:grid;grid-template-columns:32px minmax(0,1fr) auto;gap:14px;align-items:start;padding:14px 16px;
        border-top:1px solid var(--line);background:var(--panel)}
.ob-row:hover{background:#FDFBFA}
.ob-ic{width:32px;height:32px;border-radius:10px;background:var(--blue-bg);display:grid;place-items:center}
.ob-ic svg{width:16px;height:16px;fill:none;stroke:var(--blue);stroke-width:1.6}
.ob-ic.mine{background:var(--green-bg)}.ob-ic.mine svg{stroke:var(--green)}
.ob-ic.held{background:var(--red-bg)}.ob-ic.held svg{stroke:var(--red)}
.ob-t{font-size:16px;font-weight:600;color:var(--text);line-height:1.4}
.ob-t a{color:var(--text);text-decoration:none}.ob-t a:hover{color:var(--blue)}
.ob-props{display:flex;flex-wrap:wrap;gap:2px 16px;margin-top:4px;font-size:14px;color:var(--dim);line-height:1.5}
.ob-props i{font-style:normal;color:var(--muted);margin-right:5px}
.ob-props .ai-why{color:var(--dim);font-style:italic}
.ob-r{font-size:13px;color:var(--muted);white-space:nowrap;padding-top:3px}

/* tags and chips */
.tag{display:inline-block;font-size:12px;font-weight:500;padding:2px 9px;margin-left:8px;border-radius:999px;vertical-align:2px}
.tag.cat{background:var(--panel2);color:var(--dim)}
.tag.pick{background:var(--blue);color:#fff}
.tag.mine{background:var(--green-bg);color:var(--green)}
.tag.ai{font-size:12px}
.tag.ai.hi{background:var(--green-bg);color:var(--green)}
.tag.ai.mid{background:rgba(176,122,34,.1);color:var(--orange)}
.tag.ai.lo{background:var(--red-bg);color:var(--red)}
.chk{display:inline-block;font-size:12px;padding:2px 9px;margin:8px 4px 0 0;border-radius:999px}
.chk.ok{background:var(--green-bg);color:var(--green)}
.chk.no{background:var(--red-bg);color:var(--red)}
.chk-why{font-size:13px;color:var(--red);margin-left:6px}
.src-chips{display:flex;flex-wrap:wrap;gap:6px;padding:0 0 10px}
.src-chips span{font-size:13px;background:var(--panel);border:1px solid var(--line);padding:3px 10px;border-radius:999px;color:var(--dim)}
.src-chips b{color:var(--text);font-weight:600;margin-left:6px}
.rule-chips span{display:inline-block;font-size:13px;background:var(--panel);border:1px solid var(--line);color:var(--dim);
  padding:3px 10px;border-radius:999px;margin:0 4px 4px 0}
.ob-note{font-size:13px;color:var(--orange);background:rgba(176,122,34,.08);border:1px solid rgba(176,122,34,.2);
         border-radius:999px;padding:5px 12px;margin-bottom:12px;display:inline-block}

/* streamlit widgets */
[data-testid="stExpander"] details{border:1px solid var(--line);border-radius:12px;background:var(--panel);box-shadow:var(--shadow)}
[data-testid="stExpander"] summary p{font-weight:600;font-size:15px}
[data-testid="stDataFrame"]{border-radius:12px;overflow:hidden}
.st-key-teamlist [data-testid="stVerticalBlock"]{gap:0}

/* curation policy */
.policy{border:1px solid var(--line);border-radius:14px;background:var(--panel);box-shadow:var(--shadow);margin-bottom:24px;overflow:hidden}
.pol-k{display:block;font-size:14px;font-weight:600;color:var(--dim);margin-bottom:8px}
.pol-mission{padding:24px 26px;border-bottom:1px solid var(--line);background:linear-gradient(180deg,#FBF3F6,#FFFFFF)}
.pol-mission p{font-size:20px;line-height:1.5;color:var(--text);margin:0;max-width:60ch;letter-spacing:-.005em}
.pol-mission b{color:var(--blue);font-weight:600}
.pol-grid{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr)}
.pol-col{padding:20px 26px}
.pol-col.good{border-right:1px solid var(--line)}
.pol-col.good .pol-k{color:var(--green)}
.pol-col.bad .pol-k{color:var(--red)}
.pol-sub{font-size:15px;color:var(--dim);margin:0 0 12px;line-height:1.5}
.pol-chips{display:flex;flex-wrap:wrap;gap:6px}
.pol-chips span{font-size:14px;padding:4px 12px;border-radius:999px;background:var(--green-bg);color:var(--green)}
.pol-avoid{padding:10px 0;border-top:1px solid var(--line)}
.pol-avoid:first-of-type{border-top:none;padding-top:0}
.pol-avoid b{font-size:15px;color:var(--text)}
.pol-avoid p{font-size:14px;color:var(--dim);margin:3px 0 0;line-height:1.55}
.pol-foot{padding:16px 26px;border-top:1px solid var(--line);display:grid;gap:8px;background:#FCFAF8}
.pol-foot p{font-size:14px;color:var(--dim);margin:0;line-height:1.6}
.pol-foot b{color:var(--text);font-weight:600}
@media (max-width:900px){.pol-grid{grid-template-columns:1fr}.pol-col.good{border-right:none;border-bottom:1px solid var(--line)}
  .ob-stats{grid-template-columns:repeat(2,minmax(0,1fr))}}
.teach{border:1px dashed var(--line2);border-radius:12px;background:var(--panel);padding:20px 22px;max-width:760px}
.teach p{font-size:15px;color:var(--dim);line-height:1.6;margin:0 0 10px}
.teach p.teach-lead{font-size:17px;font-weight:600;color:var(--text);margin-bottom:6px}
.teach b{color:var(--text);font-weight:600}
.teach-bar{height:8px;border-radius:999px;background:var(--panel2);overflow:hidden;margin:14px 0 6px}
.teach-bar i{display:block;height:100%;background:var(--blue);border-radius:999px}
.teach p.teach-count{font-size:14px;color:var(--dim);margin:0}
.teach-ex{padding:10px 0;border-top:1px solid var(--line);font-size:15px;color:var(--text)}
.teach-ex .chk{margin:0 8px 0 0}
.teach-why{display:block;font-size:14px;color:var(--dim);margin-top:4px}
.teach p.teach-foot{font-size:13px;color:var(--muted);margin:10px 0 0}
.audience{border:1px solid var(--line);border-radius:14px;background:var(--panel);box-shadow:var(--shadow);
  padding:22px 26px;margin-bottom:18px}
.audience h3{font-size:24px;font-weight:700;letter-spacing:-.015em;color:var(--text);margin:0;padding:0}
.audience .aud-who{font-size:16px;color:var(--dim);margin:4px 0 16px}
.aud-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px}
.aud-t{background:var(--blue-bg);border-radius:10px;padding:12px 14px}
.aud-t b{font-size:15px;color:var(--blue)}
.aud-t p{font-size:14px;color:var(--text);margin:4px 0 0;line-height:1.5}
.aud-foot{margin-top:14px;display:grid;gap:4px}
.aud-foot p{font-size:15px;color:var(--dim);margin:0;line-height:1.55}
.aud-foot b{color:var(--text);font-weight:600}
@media (max-width:900px){.aud-grid{grid-template-columns:1fr 1fr}}
.aud-line{display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin:0;font-size:14px;color:var(--dim)}
.aud-line .aud-k{color:var(--muted);margin-right:2px}
.aud-line b{color:var(--text);font-weight:600;margin-right:4px}
.aud-line span:not(.aud-k){background:var(--blue-bg);color:var(--blue);padding:3px 10px;border-radius:999px;font-size:13px}
.breaker{border:1px solid rgba(177,74,64,.3);background:var(--red-bg);border-radius:12px;padding:16px 20px;margin-bottom:12px}
.breaker p{font-size:15px;color:var(--text);margin:0 0 6px;line-height:1.5}
.breaker p.br-lead{font-weight:700;color:var(--red);font-size:16px}
.breaker ul{margin:4px 0 8px 18px;padding:0}.breaker li{font-size:15px;color:var(--text);line-height:1.6}
.breaker p.br-meta{font-size:13px;color:var(--dim);margin:0}
.steps{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-bottom:14px}
.step{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px;display:grid;gap:4px;align-content:start}
.step .sn{width:26px;height:26px;border-radius:50%;background:var(--blue-bg);color:var(--blue);font-weight:700;
  font-size:14px;display:grid;place-items:center;margin-bottom:4px}
.step b{font-size:16px;color:var(--text)}
.step p{font-size:14px;color:var(--dim);margin:0;line-height:1.5}
.band{display:flex;gap:4px;border-radius:12px;overflow:hidden}
.band .seg{padding:12px 14px;min-width:0;display:grid;gap:2px}
.band .seg b{font-size:24px;font-weight:700;line-height:1.1}
.band .seg span{font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.band .lo{background:var(--red-bg)}.band .lo b,.band .lo span{color:var(--red)}
.band .mid{background:rgba(143,98,20,.1)}.band .mid b,.band .mid span{color:var(--orange)}
.band .hi{background:var(--green-bg)}.band .hi b,.band .hi span{color:var(--green)}
.aud-line{margin:0}
.venn-wrap{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(0,1fr);gap:28px;align-items:center;
  background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:20px 24px}
.venn svg{width:100%;max-width:520px;height:auto;display:block;margin:0 auto}
.venn-side{display:grid;gap:18px}
.vs-k{display:block;font-size:14px;font-weight:600;color:var(--dim);margin-bottom:8px}
.vs-k.never{color:var(--red)}.vs-k.ok{color:var(--green)}
.vs-chips{display:flex;flex-wrap:wrap;gap:6px}
.vs-chips span{font-size:14px;padding:4px 12px;border-radius:999px}
.vs-chips.never span{background:var(--red-bg);color:var(--red)}
.vs-chips.ok span{background:var(--green-bg);color:var(--green)}
.vs-block p{font-size:14px;color:var(--dim);margin:6px 0 0;line-height:1.5}
@media (max-width:900px){.steps,.venn-wrap{grid-template-columns:1fr}}
.cute h1, .ob-sec.cute .t, .journey h3{font-family:'Fredoka','Figtree',sans-serif !important;font-weight:600;letter-spacing:0}
.ob-sec.cute{margin-top:44px}
.journey{display:grid;gap:18px;margin:6px 0 10px;position:relative}
.j-step{display:grid;grid-template-columns:minmax(0,300px) minmax(0,1fr);gap:28px;align-items:center;
  background:var(--panel);border:1px solid var(--line);border-radius:22px;padding:14px 28px 14px 14px;box-shadow:var(--shadow)}
.j-step.flip{grid-template-columns:minmax(0,1fr) minmax(0,300px);padding:14px 14px 14px 28px}
.j-step.flip .j-art{order:2}
.j-art svg{width:100%;height:auto;display:block;border-radius:18px}
.j-txt{display:grid;gap:6px;justify-items:start}
.j-n{width:30px;height:30px;border-radius:50%;background:var(--blue);color:#fff;font:600 15px 'Fredoka',sans-serif;
  display:grid;place-items:center}
.journey h3{font-size:24px;color:var(--text);margin:2px 0 0;padding:0;line-height:1.2}
.j-txt p{font-size:16px;color:var(--dim);margin:0;line-height:1.5;max-width:46ch}
.j-chip{margin-top:4px;font-size:13px;font-weight:600;color:var(--blue);background:var(--blue-bg);padding:4px 12px;border-radius:999px}
@media (max-width:760px){.j-step,.j-step.flip{grid-template-columns:1fr;padding:14px}.j-step.flip .j-art{order:0}}
</style>
""", unsafe_allow_html=True)

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
                f"<span class='c'>{len(filt)}</span><span class='hint'>by reason · edit rules on the Filters page"
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
  <circle cx="210" cy="160" r="135" style="fill:var(--blue);fill-opacity:.13;stroke:var(--blue);stroke-width:1.5"/>
  <circle cx="370" cy="160" r="135" style="fill:var(--green);fill-opacity:.13;stroke:var(--green);stroke-width:1.5"/>
  <circle cx="290" cy="290" r="135" style="fill:var(--orange);fill-opacity:.13;stroke:var(--orange);stroke-width:1.5"/>
  <g font-family="Figtree,sans-serif" text-anchor="middle">
    <text x="150" y="120" font-size="17" font-weight="700" style="fill:var(--blue)">Community</text>
    <text x="150" y="140" font-size="13" style="{d}">brings people</text>
    <text x="150" y="156" font-size="13" style="{d}">together</text>
    <text x="430" y="120" font-size="17" font-weight="700" style="fill:var(--green)">Free</text>
    <text x="430" y="140" font-size="13" style="{d}">no cost, no</text>
    <text x="430" y="156" font-size="13" style="{d}">upsell</text>
    <text x="290" y="372" font-size="17" font-weight="700" style="fill:var(--orange)">Adventure</text>
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
    st.markdown("<div class='ob ob-title cute'><h1>How a pick is made</h1>"
                "<p>From a messy list of listings to Seattle showing up together.</p></div>", unsafe_allow_html=True)

    scored = trace[trace["ai_score"].notna()]
    decided = trace[trace["status"] != MERGED]
    n_kept = int(((decided["ai_score"] >= hi) & decided["status"].isin([PICK, PUBLISH])).sum())
    n_unsure = int(decided["why"].astype(str).str.startswith("AI unsure").sum())
    n_low = int((decided["filter_category"] == "AI: low relevance").sum())

    raw_events = (raw or {}).get("events_raw") or []
    n_sites = len({urlparse(e.get("source") or "").netloc for e in raw_events} - {""}) or len(SOURCE_PAGES) + len(MONTHLY_PAGES)
    upgraded = CURATOR_MODEL != OPENAI_MODEL
    steps = [
        ("We pull the listings", f"Every Monday the agent reads {n_sites} Seattle event sites.",
         f"{len(raw_events)} events found"),
        ("A low-cost model tidies them up", f"{OPENAI_MODEL} turns messy pages into clean events: date, place, cost.",
         f"{len(trace)} events after removing repeats"),
        ("A stronger model finds the gems",
         (f"{CURATOR_MODEL} reads what each event is really for and scores how much our people would love it."
          if upgraded else "Reads what each event is really for and scores how much our people would love it. "
          "Ready for a stronger model."), f"{n_kept} made the list"),
        ("Our team teaches it", "Thumbs up and down override the AI and become its examples next time.",
         f"{len(fb_rows)} team votes"),
        ("Picks become our graphic", "The week's picks go into the Seattle Unlocked template.", "Team step"),
        ("We post it", "The graphic goes up on Instagram for 80k Seattle locals.", "@seattle_forfree"),
        ("Seattle shows up", "Neighbors meet, try something new, and the city gets a little closer.", "The whole point"),
    ]
    cards = "".join(
        f"<div class='j-step{' flip' if i % 2 else ''}'>"
        f"<div class='j-art'>{illustrations.SCENES[i]()}</div>"
        f"<div class='j-txt'><span class='j-n'>{i + 1}</span><h3>{esc(t)}</h3><p>{esc(d)}</p>"
        f"<span class='j-chip'>{esc(c)}</span></div></div>"
        for i, (t, d, c) in enumerate(steps))
    st.markdown(f"<div class='ob journey'>{cards}</div>", unsafe_allow_html=True)

    # Who we curate for, and what makes a pick
    traits = "".join(f"<span>{esc(k)}</span>" for k, _ in AUDIENCE["traits"])
    st.markdown(f"""
<div class='ob ob-sec cute'><span class='t'>Who we curate for</span></div>
<div class='ob aud-line'><b>Seattle locals, 28 to 52</b>{traits}</div>
<div class='ob ob-sec cute'><span class='t'>What makes a pick</span></div>
<div class='ob venn-wrap'>
  <div class='venn'>{venn_svg()}</div>
  <div class='venn-side'>
    <div class='vs-block'><span class='vs-k never'>Never on the list</span>
      <div class='vs-chips never'><span>Sales pitches</span><span>Religious services</span><span>Partisan events</span></div></div>
    <div class='vs-block'><span class='vs-k ok'>Still welcome</span>
      <div class='vs-chips ok'><span>Diwali</span><span>Lunar New Year</span><span>MLK Day</span><span>Holiday markets</span></div>
      <p>Cultural and civic celebrations everyone shares.</p></div>
    <div class='vs-block'><span class='vs-k'>Gray areas</span><p>Go to the team, and their votes become the AI's best examples.</p></div>
  </div>
</div>""", unsafe_allow_html=True)

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
    labeled = [r for r in fb_rows if r.get("model_score") is not None]
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


# ---------- filters page ----------


def render_filters_page() -> None:
    rules = filters.load()
    st.markdown("<div class='ob ob-title'><h1>Filters</h1>"
                "<p>What gets kept off the list, and why. Every filtered event is grouped by its reason.</p></div>",
                unsafe_allow_html=True)
    filt = trace[trace["status"] == FILTERED]

    # Filtered events by reason, with an Allow switch for the team
    st.markdown(f"<div class='ob ob-sec filt'><span class='dot'></span><span class='t'>Filtered events</span>"
                f"<span class='c'>{len(filt)}</span></div>", unsafe_allow_html=True)
    if filt.empty:
        st.markdown("<div class='ob empty'>Nothing filtered this run.</div>", unsafe_allow_html=True)
    allow_now = set(rules["allow"])
    for cat_name, grp in sorted(filt.groupby("filter_category"), key=lambda g: -len(g[1])):
        with st.expander(f"{cat_name} · {len(grp)}"):
            table = pd.DataFrame({
                "Allow": False,
                "Event": grp["title"],
                "Date": grp["date"].map(day_label),
                "Matched": grp["why"].map(lambda w: str(w).split(": ", 1)[-1]),
                "Cost": grp["cost"],
                "Source": grp["site"],
                "Link": grp["link"],
            })
            if team:
                edited = st.data_editor(
                    table, hide_index=True, width="stretch", key=f"allow-{cat_name}",
                    column_config={"Allow": st.column_config.CheckboxColumn(help="Keep this event on the list"),
                                   "Link": st.column_config.LinkColumn(display_text="open")},
                    disabled=[c for c in table.columns if c != "Allow"])
                picked = grp.loc[edited["Allow"].values, "filter_key"].tolist()
                if picked and st.button(f"Allow {len(picked)} selected", key=f"allow-btn-{cat_name}",
                                        type="primary"):
                    rules["allow"] = sorted(allow_now | set(picked))
                    filters.save(rules)
                    st.rerun()
            else:
                st.dataframe(table.drop(columns=["Allow"]), hide_index=True, width="stretch",
                             column_config={"Link": st.column_config.LinkColumn(display_text="open")})

    # The rules themselves
    st.markdown("<div class='ob ob-sec rec' style='margin-top:26px'><span class='dot'></span>"
                "<span class='t'>Rules</span></div>", unsafe_allow_html=True)
    if not team:
        on = lambda x: "on" if x else "off"
        st.markdown(
            f"<div class='ob empty' style='color:var(--dim)'>"
            f"Price listed: <b>{on(rules['price_listed'])}</b> · Tickets required: <b>{on(rules['tickets'])}</b> · "
            f"Price in description: <b>{on(rules['price_in_text'])}</b></div>", unsafe_allow_html=True)
        for topic, terms in rules["topics"].items():
            st.markdown(f"<div class='ob' style='margin-top:12px'><b>{esc(topic)}</b><div class='rule-chips' "
                        f"style='margin-top:6px'>" + "".join(f"<span>{esc(t)}</span>" for t in terms)
                        + "</div></div>", unsafe_allow_html=True)
        st.caption("Sign in to change the rules.")
        return

    with st.form("rules"):
        st.markdown("**Free events only**")
        c1, c2, c3 = st.columns(3)
        price = c1.toggle("Price listed", value=rules["price_listed"],
                          help="Filter events whose cost shows a price, like $15 or Varies.")
        tickets = c2.toggle("Tickets required", value=rules["tickets"],
                            help="Filter events with ticket language, or marked ticketed by the extractor.")
        price_text = c3.toggle("Price in description", value=rules["price_in_text"],
                               help="Filter events with a dollar amount in the title or description.")
        ticket_terms = st.text_area("Ticket words (one per line)", "\n".join(rules["ticket_terms"]), height=140)

        st.markdown("**Topics to keep off the list**")
        topic_edits, remove = {}, set()
        for topic, terms in rules["topics"].items():
            a, b = st.columns([5, 1], vertical_alignment="bottom")
            topic_edits[topic] = a.text_area(f"{topic} (one word or phrase per line)", "\n".join(terms),
                                             height=120, key=f"topic-{topic}")
            if b.checkbox("Remove", key=f"rm-topic-{topic}"):
                remove.add(topic)
        a, b = st.columns([2, 5])
        new_name = a.text_input("New topic", placeholder="e.g. Fundraisers")
        new_terms = b.text_input("Words for the new topic, comma separated", placeholder="gala, fundraiser, donate")

        if st.form_submit_button("Save rules", type="primary"):
            lines = lambda txt: [t.strip() for t in txt.replace(",", "\n").splitlines() if t.strip()]
            rules.update(price_listed=price, tickets=tickets, price_in_text=price_text,
                         ticket_terms=lines(ticket_terms))
            rules["topics"] = {t: lines(v) for t, v in topic_edits.items() if t not in remove}
            if new_name.strip() and new_terms.strip():
                rules["topics"][new_name.strip()] = lines(new_terms)
            filters.save(rules)
            st.rerun()

    if rules["allow"]:
        with st.expander(f"Allowed events · {len(rules['allow'])}"):
            keep = st.multiselect("Allowed (remove to filter them again)", rules["allow"], default=rules["allow"])
            if st.button("Update allowed list") and set(keep) != set(rules["allow"]):
                rules["allow"] = keep
                filters.save(rules)
                st.rerun()
    if st.button("Reset all rules to defaults"):
        filters.reset()
        st.rerun()


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
    st.button("AI curation", key="nav-curation", width="stretch", on_click=go_to, args=("curation",),
              type="primary" if state.section == "curation" else "secondary")
    st.button("Clients", key="nav-clients", width="stretch", on_click=go_to, args=("clients",),
              type="primary" if state.section == "clients" else "secondary")
    st.button(f"Filters  ·  {int((trace['status'] == FILTERED).sum())}", key="nav-filters", width="stretch",
              on_click=go_to, args=("filters",),
              type="primary" if state.section == "filters" else "secondary")

# ---------- page ----------
if state.section == "curation":
    render_curation_page()
elif state.section == "clients":
    crm_view.render(team)
elif state.section == "filters":
    render_filters_page()
elif state.section == "ontology":
    st.markdown("<div class='ob ob-title'><h1>Ontology of events</h1>"
                "<p>How Seattle's free events connect: categories, neighborhoods, venues, and sources.</p></div>",
                unsafe_allow_html=True)
    render_ontology(res["trace"], labels)
else:
    render_breaker()
    st.markdown("<div class='ob ob-title'><h1>Seattle Free Events</h1><p>Free things worth leaving the house for, "
                "picked for outgoing, community-minded Seattleites. No sales pitches.</p></div>",
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
