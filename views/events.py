"""End result: the list we post, month by month, plus what was held and filtered and why."""
from collections import Counter
from datetime import date

import pandas as pd
import streamlit as st

import breaker
import custom_events
import feedback
import snapshot
from agents.synthesizer import FILTERED, MERGED, PICK, PUBLISH, REVIEW, SHEET_COLUMNS
from ui.components import day_label, esc, event_row, filtered_row, sheet_rows


def render(ctx) -> None:
    render_breaker(ctx.team)
    st.markdown("<div class='ob ob-title'><h1>End result</h1><p>The list we post: free things worth leaving the house for, "
                "picked for outgoing, community-minded Seattleites.</p></div>",
                unsafe_allow_html=True)
    v = st.session_state.view
    if v in ctx.labels:
        m = ctx.months[ctx.labels.index(v)]
        render_month(ctx.trace[ctx.trace["month"] == (m.year, m.month)], v, v, ctx)
    elif v == "Past or undated":
        render_month(ctx.other, "Past, undated, or later", None, ctx)
    elif v == "Added by you":
        st.markdown("<div class='ob'><div class='ob-head'><h2>Added by you</h2></div></div>", unsafe_allow_html=True)
        status_by_id = {t["custom_id"]: t for _, t in ctx.trace.iterrows() if t["custom"]}
        for e in ctx.mine:
            t = status_by_id.get(e["custom_id"])
            a, b = st.columns([6, 1], vertical_alignment="center")
            if t is not None:
                a.markdown(f"<div class='ob ob-list'>{event_row(t['status'], t, held=t['status'] == REVIEW, votes=ctx.votes)}</div>",
                           unsafe_allow_html=True)
            if ctx.team and b.button("Remove", key=f"rm-{e['custom_id']}", width="stretch"):
                custom_events.remove(e["custom_id"])
                st.rerun()


def render_breaker(team: bool) -> None:
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


def record_table(df: pd.DataFrame, key: str, titles_by_id: dict) -> None:
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


def cast_vote(t: dict, value: int, votes: dict) -> None:
    """Thumbs up/down. Clicking the same thumb again removes the vote."""
    if votes.get(t["key"]) == value:
        feedback.clear(t["key"])
    else:
        curation = {"score": t.get("ai_score"), "intent": t.get("ai_intent")}
        feedback.vote({**t, "description": t.get("description", "")}, value, curation)


def team_rows(group: pd.DataFrame, held: bool, votes: dict) -> None:
    for i, (_, t) in enumerate(group.iterrows(), 1):
        a, b, c = st.columns([24, 1, 1], gap="small", vertical_alignment="center")
        a.markdown(f"<div class='ob'>{event_row(i, t, held=held, votes=votes)}</div>", unsafe_allow_html=True)
        v = votes.get(t["key"])
        rec = t.to_dict()
        b.button("", icon=":material/thumb_up:", key=f"up-{t['key']}-{t['id']}", help="Feature events like this",
                 type="primary" if v == 1 else "tertiary", on_click=cast_vote, args=(rec, 1, votes))
        c.button("", icon=":material/thumb_down:", key=f"dn-{t['key']}-{t['id']}", help="Don't feature events like this",
                 type="primary" if v == -1 else "tertiary", on_click=cast_vote, args=(rec, -1, votes))


def render_month(df: pd.DataFrame, label: str, file_label: str | None, ctx) -> None:
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
    if ctx.team:  # pipeline numbers are for the team; readers just get the list
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
            rows += event_row(n, t, votes=ctx.votes)
        weekend = " weekend" if isinstance(d, date) and d.weekday() >= 5 else ""
        head = (f"<span class='wd'>{d:%a}</span>{d:%B} {d.day}" if isinstance(d, date) and d != date.max
                else "No date")
        body += (f"<details class='ob-acc-day'{day_open}><summary class='ob-day{weekend}'>"
                 f"<span class='chev'></span>{head}<span class='n'>{len(group)} event{'s' if len(group) != 1 else ''}</span></summary>"
                 f"{rows}</details>")
    if not body:
        body = "<div class='ob-empty-in'>No events ready for this month yet.</div>"
    if ctx.team:
        st.markdown(f"<div class='ob ob-sec' style='margin-top:18px'><span class='dot'></span>"
                    f"<span class='t'>Available</span><span class='c'>{len(available)}</span>"
                    f"<span class='hint'>thumbs teach the AI curator</span></div>", unsafe_allow_html=True)
        for d, group in available.groupby("_d", sort=True):
            label_d = f"{d:%a %B} {d.day}" if isinstance(d, date) and d != date.max else "No date"
            with st.expander(f"{label_d} · {len(group)} event{'s' if len(group) != 1 else ''}", expanded=not collapse):
                team_rows(group, held=False, votes=ctx.votes)
    else:
        st.markdown(f"<details class='ob ob-acc' open><summary class='ob-sec'><span class='chev'></span>"
                    f"<span class='dot'></span><span class='t'>Available</span><span class='c'>{len(available)}</span>"
                    f"</summary><div class='ob-list'>{body}</div></details>", unsafe_allow_html=True)

    if ctx.team and file_label and not available.empty:
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
    if ctx.team and not held.empty:
        with st.expander(f"Held for review · {len(held)}  (AI unsure and missing details)", expanded=not collapse):
            team_rows(held, held=True, votes=ctx.votes)
    rows = "".join(event_row(i, t, held=True, votes=ctx.votes) for i, (_, t) in enumerate(held.iterrows(), 1)) \
        or "<div class='ob-empty-in'>Nothing held.</div>"
    if not ctx.team or held.empty:
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
    if ctx.team and not ai_out.empty:
        with st.expander(f"Filtered by the AI or your team · {len(ai_out)}  (thumbs up to bring one back)"):
            team_rows(ai_out, held=True, votes=ctx.votes)

    # 4. Full record
    st.write("")
    with st.expander(f"Full record · {len(df)} events, every source and check", expanded=False):
        st.markdown("<div class='ob src-chips' style='border:none;padding:0 0 8px;background:none'>" + "".join(
            f"<span>{esc(s)}<b>{k}</b></span>" for s, k in sources.most_common()) + "</div>",
            unsafe_allow_html=True)
        record_table(df, key=f"rec-{label}", titles_by_id=ctx.titles_by_id)
