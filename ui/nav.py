"""Navigation: session-state only (section + view), same buttons and keys as before. No URL params."""
import streamlit as st

SECTIONS = ("curation", "ontology", "press", "events")


def go_to(section: str, view: str | None = None) -> None:
    state = st.session_state
    state.section = section
    if view:
        state.view = view


def init(labels: list[str], month_views: list[tuple]) -> None:
    state = st.session_state
    state.setdefault("section", "curation")
    if state.section not in SECTIONS:
        state.section = "curation"
    if state.get("view") not in [v for v, _ in month_views]:
        state.view = labels[0]


def render(nav_box, month_views: list[tuple]) -> None:
    state = st.session_state
    with nav_box:
        st.button("How it works", key="nav-curation", width="stretch", on_click=go_to, args=("curation",),
                  type="primary" if state.section == "curation" else "secondary")
        st.button("Ontology of events", key="nav-onto", width="stretch", on_click=go_to, args=("ontology",),
                  type="primary" if state.section == "ontology" else "secondary")
        st.button("Press and clients", key="nav-press", width="stretch", on_click=go_to, args=("press",),
                  type="primary" if state.section == "press" else "secondary")
        st.button("End result", key="nav-events", width="stretch", on_click=go_to, args=("events",),
                  type="primary" if state.section == "events" else "secondary")
        if state.section == "events":
            with st.container(key="nav-months"):
                for v, n in month_views:
                    st.button(f"{v}  ·  {n}", key=f"nav-{v}", width="stretch", on_click=go_to, args=("events", v),
                              type="primary" if state.view == v else "tertiary")
