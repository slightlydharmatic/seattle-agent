"""The sidebar: brand, the slot for navigation, team controls, run status, and sign-in."""
import hmac
from datetime import date

import streamlit as st

import custom_events
from agents.reasoner import CATEGORIES
from ui.data import team_password

CATEGORY_OPTIONS = ["Auto"] + list(CATEGORIES) + ["Community"]


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


def start(team: bool, snap: dict | None):
    """Top of the sidebar. Returns (nav_box, (use_sample, query, n_months, picks, include_paid, go))."""
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
    return nav_box, (use_sample, query, n_months, picks, include_paid, go)


def status(ctx) -> None:
    """Bottom of the sidebar: data freshness, where team work is saved, and sign in / out."""
    with st.sidebar:
        st.caption("Sample data" if ctx.is_sample else f"Updated {ctx.as_of:%b} {ctx.as_of.day}, {ctx.as_of.year}" if ctx.as_of else "")
        if ctx.team:
            import kvstore
            if kvstore.is_connected():
                st.caption(":material/cloud_done: Team work saved to Supabase")
            else:
                st.caption(":material/warning: Votes and filter edits are saved on this server only "
                           "and reset when the app restarts. Connect Supabase to keep them.")

        st.divider()
        if ctx.team:
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
