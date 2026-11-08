"""Ontology of events: when Seattle's free events happen, what they are, and who hosts them."""
from datetime import date

import streamlit as st

import ontology
from ui.components import esc

FULL_DAY = dict(zip(ontology.DAYS, ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]))
INK, PERI, SOFT = "#1E2A47", "#5469C4", "#D9DEF3"

CSS = """<style>
.on-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:16px;margin:6px 0 30px}
.on-card{background:#fff;border:1px solid var(--line);border-radius:14px;padding:20px 20px 18px;box-shadow:var(--shadow)}
.on-k{font-size:12px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#5469C4}
.on-h{font-size:19px;font-weight:600;color:#1E2A47;margin:6px 0 16px;line-height:1.3;letter-spacing:-.01em}
.on-days{display:flex;align-items:flex-end;gap:8px;height:230px}
.on-days div{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;height:100%;gap:6px}
.on-days i{display:block;width:100%;border-radius:6px 6px 3px 3px;min-height:3px}
.on-days b{font-size:12px;font-weight:600;color:#1E2A47;font-variant-numeric:tabular-nums}
.on-days span{font-size:12px;color:var(--dim)}
.on-bar{display:grid;grid-template-columns:1fr 34px;align-items:center;gap:10px;margin:0 0 9px}
.on-bar .l{position:relative;font-size:14px;color:#1E2A47;padding:5px 10px;border-radius:6px;overflow:hidden;
           white-space:nowrap;text-overflow:ellipsis}
.on-bar .l i{position:absolute;inset:0 auto 0 0;border-radius:6px;z-index:0}
.on-bar .l span{position:relative;z-index:1}
.on-bar b{font-size:13px;font-weight:600;color:#1E2A47;text-align:right;font-variant-numeric:tabular-nums}
.on-bar.dim .l, .on-bar.dim b{color:var(--dim)}
.on-note{font-size:12.5px;color:var(--dim);margin-top:12px;line-height:1.45}
.on-sec{font-size:19px;font-weight:600;color:#1E2A47;margin:4px 0 2px;letter-spacing:-.01em}
.on-sub{font-size:14px;color:var(--dim);margin:0 0 14px}
.on-heat{width:100%;border-collapse:separate;border-spacing:4px;font-size:13px;border:none !important}
.on-heat tr, .on-heat th, .on-heat td{border:none !important;background-clip:padding-box}
.on-heat tr:nth-child(even){background:transparent !important}
.on-heat th{font-weight:600;color:var(--dim);text-align:center;padding:2px 0}
.on-heat th:first-child{text-align:left}
.on-heat td{text-align:center;border-radius:6px;height:34px;font-variant-numeric:tabular-nums}
.on-heat td:first-child{text-align:left;color:#1E2A47;font-weight:500;padding-right:10px;white-space:nowrap}
.on-empty{color:var(--dim);font-size:15px;padding:30px 0}
</style>"""


def render(ctx) -> None:
    st.markdown("<div class='ob ob-title'><h1>Ontology of events</h1>"
                "<p>What Seattle's free events look like: when they happen, what they are, and who puts them on.</p>"
                "</div>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1])
    month = c1.selectbox("Month", ["All months"] + ctx.labels, key="onto-month")
    scope = c2.radio("Events", ["Free and live", "Everything pulled"], horizontal=True, key="onto-scope")
    rows = [t for t in ctx.res["trace"] if month == "All months"
            or (isinstance(t.get("date"), date) and f"{t['date']:%B %Y}" == month)]
    p = ontology.profile(rows, live_only=scope == "Free and live")
    if not p["n"]:
        st.markdown(CSS + "<div class='on-empty'>No events here yet. Try another month, or switch to everything pulled."
                    "</div>", unsafe_allow_html=True)
        return
    st.markdown(CSS + "<div class='on-grid'>" + days_card(p["days"]) + kinds_card(p["kinds"]) + hosts_card(p["hosts"])
                + "</div>" + heatmap(p["day_kind"], p["kinds"]), unsafe_allow_html=True)


def days_card(days: dict) -> str:
    top = max(days.values()) or 1
    peak = max(days, key=days.get)
    cols = "".join(
        f"<div><b>{n or ''}</b><i style='height:{max(n / top * 100, 2):.0f}%;background:{PERI if d == peak else SOFT}'>"
        f"</i><span>{d}</span></div>" for d, n in days.items())
    weekend = days["Fri"] + days["Sat"] + days["Sun"]
    total = sum(days.values()) or 1
    return (f"<div class='on-card'><div class='on-k'>When</div><div class='on-h'>{FULL_DAY[peak]} is the busiest day</div>"
            f"<div class='on-days'>{cols}</div>"
            f"<div class='on-note'>{weekend / total:.0%} land Friday to Sunday.</div></div>")


def bars(counts, k: int = 8, dim: str | None = None) -> str:
    items = [(name, n) for name, n in counts.most_common() if name != dim][:k]
    if dim and counts.get(dim):
        items.append((dim, counts[dim]))
    top = max((n for _, n in items), default=1)
    return "".join(
        f"<div class='on-bar{' dim' if name == dim else ''}'><div class='l'>"
        f"<i style='width:{n / top * 100:.0f}%;background:{'#EEEDF0' if name == dim else SOFT if i else '#C4CCEE'}'></i>"
        f"<span>{esc(name)}</span></div><b>{n}</b></div>" for i, (name, n) in enumerate(items))


def kinds_card(kinds) -> str:
    top = kinds.most_common(1)[0][0]
    return (f"<div class='on-card'><div class='on-k'>What</div><div class='on-h'>{esc(top)} leads</div>"
            f"{bars(kinds)}</div>")


def hosts_card(hosts) -> str:
    known = [(h, n) for h, n in hosts.most_common() if h != ontology.UNSURE]
    head = f"{known[0][0]} host the most" if known else "Hosts still unknown"
    return (f"<div class='on-card'><div class='on-k'>Who hosts</div><div class='on-h'>{esc(head)}</div>"
            f"{bars(hosts, dim=ontology.UNSURE)}"
            "<div class='on-note'>Read from the venue name. Next: the AI judge tags the host directly.</div></div>")


def heatmap(day_kind, kinds, k: int = 7) -> str:
    types = [t for t, _ in kinds.most_common(k)]
    top = max(day_kind.values(), default=1) or 1
    head = "<tr><th></th>" + "".join(f"<th>{d}</th>" for d in ontology.DAYS) + "</tr>"

    def cell(n):
        if not n:
            return "<td style='background:#F6F5F8;color:#B8B4BF'>·</td>"
        a = 0.12 + 0.78 * n / top
        return f"<td style='background:rgba(84,105,196,{a:.2f});color:{'#fff' if a > .55 else INK}'>{n}</td>"
    body = "".join(f"<tr><td>{esc(t)}</td>" + "".join(cell(day_kind.get((t, d), 0)) for d in ontology.DAYS)
                   + "</tr>" for t in types)
    return ("<div class='on-card'><div class='on-sec'>What happens each day</div>"
            "<div class='on-sub'>Darker means more events. Read across to plan a week.</div>"
            f"<table class='on-heat'>{head}{body}</table></div>")
