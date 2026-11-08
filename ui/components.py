"""Pure render helpers: data in, HTML string (or DataFrame) out. No st calls in here."""
import html
from datetime import date
from urllib.parse import urlparse

import pandas as pd

from agents.synthesizer import PICK, SHEET_COLUMNS

ICON = ("<svg viewBox='0 0 16 16'><rect x='2' y='3' width='12' height='11' rx='1.5'/>"
        "<path d='M2 6.5h12M5.5 1.5v3M10.5 1.5v3'/></svg>")


def esc(x) -> str:
    # "$" is escaped too: Streamlit markdown would otherwise read "$20 ... $50" as math.
    return html.escape(str(x or "")).replace("$", "&#36;")


def day_label(d) -> str:
    return f"{d:%a %b} {d.day}" if isinstance(d, date) and d != date.max else "No date"


def site(url: str) -> str:
    return urlparse(url).netloc.removeprefix("www.") if str(url).startswith("http") else (url or "unknown")


def add_months(d: date, n: int) -> date:
    y, m = divmod(d.month - 1 + n, 12)
    return date(d.year + y, m + 1, 1)


def checks_html(t: pd.Series) -> str:
    out = ""
    for c in t["checks"] or []:
        mark = "✓" if c["passed"] else "✕"
        out += f"<span class='chk {'ok' if c['passed'] else 'no'}'>{mark} {esc(c['check'])}</span>"
    fails = [c["detail"] for c in (t["checks"] or []) if not c["passed"]]
    if fails:
        out += f"<span class='chk-why'>{esc(', '.join(fails))}</span>"
    return out


def ai_tag(t, votes: dict) -> str:
    score = t.get("ai_score")
    if score is None or pd.isna(score):
        return ""
    score = int(score)
    level = "hi" if score >= 70 else ("mid" if score >= 40 else "lo")
    vote = votes.get(t.get("key"))
    team_mark = " · team ▲" if vote == 1 else (" · team ▼" if vote == -1 else "")
    return (f"<span class='tag ai {level}' title='{esc(t.get('ai_reason'))}'>AI {score} · "
            f"{esc(t.get('ai_intent'))}{team_mark}</span>")


def event_row(n, t: pd.Series, held: bool = False, votes: dict | None = None) -> str:
    title = esc(t["title"]) or "(no title)"
    if t["link"]:
        title = f"<a href='{esc(t['link'])}' target='_blank'>{title}</a>"
    tags = f"<span class='tag cat'>{esc(t['category'])}</span>" if not held and t["category"] else ""
    if t["status"] == PICK:
        tags += "<span class='tag pick'>Pick</span>"
    if t["custom"]:
        tags += "<span class='tag mine'>Added by you</span>"
    tags += ai_tag(t, votes or {})
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


def sheet_rows(available: pd.DataFrame) -> pd.DataFrame:
    rows = [{
        "title": t["title"], "date": f"{t['date']:%B} {t['date'].day}", "time": t["time"],
        "spot": t["venue"], "hood": t["neighborhood"], "cat": t["category"],
        "desc": t["description"], "cost": t["cost"], "link": t["link"],
        "pick": t["status"] == PICK,
    } for _, t in available.iterrows()]
    return pd.DataFrame(rows, columns=SHEET_COLUMNS)


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
