"""The Clients section of the app.

Public: the pipeline with every client name, email, and deal title hidden.
Team (signed in): real names, plus controls to sort clients, move deals, and sync Gmail.
"""
import html
import os
from collections import Counter
from datetime import datetime

import pandas as pd
import streamlit as st

from crm import store as crm_store
from crm.model import CLIENT_TYPES, STAGES, UNSORTED, masked
from crm.sample import sample_db

STAGE_COLOR = ["#D29A3A", "#A04D74", "#5E8C7A", "#B9AFBF"]


def esc(x) -> str:
    return html.escape(str(x or "")).replace("$", "&#36;")


def _when(iso) -> str:
    try:
        d = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
        return f"{d:%b} {d.day}"
    except ValueError:
        return ""


def load() -> tuple[dict, str, object | None]:
    """Return (data, source, store). Source is 'supabase', 'local', or 'sample'."""
    if crm_store.is_connected():
        s = crm_store.get_store()
        return s.all(), "supabase", s
    local = crm_store.LocalStore()
    db = local.all()
    if db["clients"]:
        return db, "local", local
    return sample_db(), "sample", local


def build_rows(db: dict) -> list[dict]:
    """One row per client, with its open deal and email activity."""
    deals_by_client = {}
    for d in db["deals"]:
        deals_by_client.setdefault(d["client_id"], []).append(d)
    emails_by_client = Counter(e["client_id"] for e in db["emails"])
    last_email = {}
    for e in db["emails"]:
        if (e.get("received_at") or "") > last_email.get(e["client_id"], ""):
            last_email[e["client_id"]] = e["received_at"] or ""
    rows = []
    for c in db["clients"]:
        deals = sorted(deals_by_client.get(c["id"], []), key=lambda d: d.get("updated_at") or "", reverse=True)
        for d in deals or [None]:
            rows.append({
                "client": c, "deal": d,
                "stage": d["stage"] if d else None,
                "type": c.get("client_type") or UNSORTED,
                "emails": emails_by_client[c["id"]],
                "last": last_email.get(c["id"], c.get("created_at") or ""),
            })
    return rows


def card(r: dict, team: bool) -> str:
    c, d = r["client"], r["deal"]
    title = esc(c["name"]) if team else esc(masked(c))
    sub = (esc(d["title"]) if (team and d) else "") or ""
    meta = f"{esc(r['type'])} · {r['emails']} email{'s' if r['emails'] != 1 else ''} · last {_when(r['last'])}"
    if not team:
        meta = f"{r['emails']} email{'s' if r['emails'] != 1 else ''} · last {_when(r['last'])}"
    return (f"<div class='crm-card'><div class='crm-name'>{title}</div>"
            + (f"<div class='crm-deal'>{sub}</div>" if sub else "")
            + f"<div class='crm-meta'>{meta}</div></div>")


def render(team: bool) -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    db, source, store = load()
    rows = build_rows(db)
    deal_rows = [r for r in rows if r["deal"]]
    st.markdown("<div class='ob ob-title'><h1>Client pipeline</h1>"
                f"<p>{'Every client and where each deal stands.' if team else 'Where every deal stands. Client names are hidden.'}</p></div>",
                unsafe_allow_html=True)
    if source == "sample":
        st.markdown("<div class='ob ob-note'>Sample data. These are made-up clients, not real ones.</div>",
                    unsafe_allow_html=True)

    by_stage = Counter(r["stage"] for r in deal_rows)
    by_type = Counter(c.get("client_type") or UNSORTED for c in db["clients"])
    stats = [("Clients", len(db["clients"])), ("Open deals", len(deal_rows) - by_stage[STAGES[3]]),
             ("Awaiting invoice", by_stage[STAGES[2]]), ("Fully complete", by_stage[STAGES[3]]),
             ("Emails logged", len(db["emails"])), ("To sort", by_type[UNSORTED])]
    st.markdown("<div class='ob'><div class='ob-stats'>" + "".join(
        f"<div class='ob-stat'><span>{k}</span><b>{v}</b></div>" for k, v in stats) + "</div></div>",
        unsafe_allow_html=True)
    st.write("")

    # Pipeline board: one column per stage
    cols = st.columns(4, gap="small")
    for i, (col, stage) in enumerate(zip(cols, STAGES)):
        items = sorted([r for r in deal_rows if r["stage"] == stage], key=lambda r: r["last"], reverse=True)
        col.markdown(
            f"<div class='crm-col'><div class='crm-head' style='border-top-color:{STAGE_COLOR[i]}'>"
            f"<span>{i + 1} · {esc(stage)}</span><b>{len(items)}</b></div>"
            + ("".join(card(r, team) for r in items) or "<div class='crm-empty'>None</div>") + "</div>",
            unsafe_allow_html=True)

    # Breakdown and activity
    a, b = st.columns([2, 3], gap="large")
    with a:
        st.markdown("<div class='ob ob-sec'><span class='dot'></span><span class='t'>Clients by type</span></div>",
                    unsafe_allow_html=True)
        order = CLIENT_TYPES + [UNSORTED]
        st.dataframe(pd.DataFrame([{"Type": t, "Clients": by_type[t]} for t in order if by_type[t]]),
                     hide_index=True, width="stretch")
    with b:
        st.markdown("<div class='ob ob-sec rec'><span class='dot'></span><span class='t'>Emails per week</span></div>",
                    unsafe_allow_html=True)
        weeks = pd.to_datetime(pd.Series([e.get("received_at") for e in db["emails"]]), errors="coerce", utc=True)
        weeks = weeks.dropna().dt.tz_convert(None).dt.to_period("W").dt.start_time
        if not weeks.empty:
            import altair as alt
            wk = weeks.value_counts().sort_index().reset_index()
            wk.columns = ["week", "emails"]
            wk["label"] = wk["week"].map(lambda d: f"{d:%b} {d.day}")
            st.altair_chart(
                alt.Chart(wk).mark_bar(color="#A04D74", cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
                    x=alt.X("label:N", sort=None, title="Week of", axis=alt.Axis(labelAngle=0)),
                    y=alt.Y("emails:Q", title=None, axis=alt.Axis(tickMinStep=1)),
                    tooltip=["label", "emails"]).properties(height=220),
                width="stretch")

    if not team:
        st.caption("Sign in to see client names and update deals.")
        return
    render_team_tools(db, rows, source, store)


def render_team_tools(db: dict, rows: list[dict], source: str, store) -> None:
    st.markdown("<div class='ob ob-sec' style='margin-top:26px'><span class='dot'></span>"
                "<span class='t'>Manage</span></div>", unsafe_allow_html=True)
    if source == "sample":
        st.info("You're looking at sample clients. Connect Supabase (or add a client below) to start for real.")
    if source == "local":
        st.caption("Saved to data/crm.json on this machine. Connect Supabase so changes are permanent and shared.")

    unsorted = [c for c in db["clients"] if (c.get("client_type") or UNSORTED) == UNSORTED]
    if unsorted and source != "sample":
        with st.expander(f"Sort new clients · {len(unsorted)}", expanded=True):
            for c in unsorted:
                x, y, z = st.columns([3, 2, 1], vertical_alignment="bottom")
                x.markdown(f"**{c['name']}**  \n{c.get('email', '')}")
                t = y.selectbox("Type", CLIENT_TYPES, key=f"type-{c['id']}", label_visibility="collapsed")
                if z.button("Save", key=f"save-type-{c['id']}"):
                    crm_store.set_type(store, c["id"], t)
                    st.rerun()

    deal_rows = [r for r in rows if r["deal"]]
    if deal_rows and source != "sample":
        with st.expander("Update a deal", expanded=False):
            labels = {f"{r['client']['name']} · {r['deal']['title']}": r for r in deal_rows}
            pick = st.selectbox("Deal", list(labels))
            r = labels[pick]
            c1, c2 = st.columns(2)
            stage = c1.selectbox("Stage", STAGES, index=STAGES.index(r["stage"]), key="deal-stage")
            ctype = c2.selectbox("Client type", CLIENT_TYPES + [UNSORTED],
                                 index=(CLIENT_TYPES + [UNSORTED]).index(r["type"]), key="deal-type")
            if st.button("Save changes", type="primary"):
                if stage != r["stage"]:
                    crm_store.set_stage(store, r["deal"]["id"], stage)
                if ctype != r["type"]:
                    crm_store.set_type(store, r["client"]["id"], ctype)
                st.rerun()

    with st.expander("Add a client by hand"):
        with st.form("add-client", border=False):
            c1, c2 = st.columns(2)
            name = c1.text_input("Name *")
            email = c2.text_input("Email")
            c3, c4 = st.columns(2)
            ctype = c3.selectbox("Type", CLIENT_TYPES)
            stage = c4.selectbox("Stage", STAGES)
            title = st.text_input("Deal", placeholder="e.g. Holiday feed post")
            if st.form_submit_button("Add client", type="primary"):
                if not name.strip():
                    st.error("Add a name.")
                else:
                    crm_store.add_client(store, name.strip(), email.strip(), ctype, title.strip(), stage)
                    st.rerun()

    if os.getenv("GMAIL_TOKEN_JSON"):
        if st.button("Sync Gmail now"):
            from crm.gmail_sync import sync
            with st.spinner("Reading client emails..."):
                try:
                    counts = sync(store=store)
                    st.success(f"{counts['new client']} new clients, {counts['logged']} emails logged.")
                except Exception as err:  # setup or Gmail errors
                    st.error(f"Gmail sync failed: {err}")
    else:
        st.caption("Gmail sync turns on once GMAIL_TOKEN_JSON is set (see the README).")

    with st.expander("All clients"):
        st.dataframe(pd.DataFrame([{
            "Name": r["client"]["name"], "Email": r["client"].get("email", ""), "Type": r["type"],
            "Deal": r["deal"]["title"] if r["deal"] else "", "Stage": r["stage"] or "",
            "Emails": r["emails"], "Last email": _when(r["last"])} for r in rows]),
            hide_index=True, width="stretch")


CSS = """
<style>
.crm-col{background:#F6F2EF;border-radius:12px;min-height:220px;margin-bottom:18px;padding-bottom:4px}
.crm-head{display:flex;justify-content:space-between;align-items:center;padding:12px 14px 8px;font-size:15px;font-weight:600;
  color:var(--text);border-top:3px solid;border-radius:12px 12px 0 0}
.crm-head b{font-size:13px;font-weight:500;color:var(--muted)}
.crm-card{margin:8px;padding:12px 14px;background:#fff;border:1px solid var(--line);border-radius:10px;box-shadow:var(--shadow)}
.crm-name{font-size:15px;font-weight:600;color:var(--text)}
.crm-deal{font-size:14px;color:var(--dim);margin-top:2px}
.crm-meta{font-size:13px;color:var(--muted);margin-top:6px}
.crm-empty{color:var(--muted);font-size:14px;padding:14px}
</style>
"""
