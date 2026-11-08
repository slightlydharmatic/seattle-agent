"""Seattle Unlocked event desk: every event pulled, where it came from, and what's live, by month.

    streamlit run app.py

Entry point only: page config, theme, sidebar, the team's run actions, navigation, and
which page to draw. Pages live in views/, shared pieces in ui/. See CLAUDE.md.
"""
import streamlit as st

import snapshot
from ui import data, nav, sidebar, theme
from views import curation as curation_view
from views import events as events_view
from views import ontology as ontology_view
from views import press as press_view

st.set_page_config(page_title="Seattle Unlocked · Event Desk", layout="wide")

theme.inject()

# Sidebar top: brand, a slot for navigation (filled once months are known), team controls.
team = st.session_state.get("team", False)
snap = snapshot.load()
nav_box, (use_sample, query, n_months, picks, include_paid, go) = sidebar.start(team, snap)

# Team actions: a live search, then AI curation if one was asked for.
if go:
    snap, use_sample = data.run_live_search(query), False
snap = data.run_curation(snap)

# Everything a page needs, in one object.
ctx = data.load_ctx(snap, use_sample, n_months, picks, include_paid, team)

sidebar.status(ctx)

if ctx.is_sample:
    st.markdown("<div class='ob ob-note'>Sample data. These are example events, not live listings.</div>",
                unsafe_allow_html=True)

nav.init(ctx.labels, ctx.month_views)
nav.render(nav_box, ctx.month_views)

section = st.session_state.section
if section == "curation":
    curation_view.render(ctx)
elif section == "ontology":
    ontology_view.render(ctx)
elif section == "press":
    press_view.render(ctx)
else:
    events_view.render(ctx)
