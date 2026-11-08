"""Ontology of events: how categories, neighborhoods, venues, and sources connect."""
from collections import Counter
from datetime import date

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

import ontology
from agents.synthesizer import MERGED
from config import PROJECT_DIR


def render(ctx) -> None:
    st.markdown("<div class='ob ob-title'><h1>Ontology of events</h1>"
                "<p>How Seattle's free events connect: categories, neighborhoods, venues, and sources.</p></div>",
                unsafe_allow_html=True)
    render_ontology(ctx.res["trace"], ctx.labels)


@st.cache_resource
def vis_js() -> str:
    """The vis-network library, bundled in assets/ so the graph never depends on a CDN."""
    return (PROJECT_DIR / "assets" / "vis-network.min.js").read_text()


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
