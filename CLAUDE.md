# Seattle Unlocked event desk

A Streamlit app that finds free Seattle events and curates them for the Seattle Unlocked Instagram (@seattle_forfree). A weekly pipeline (LangGraph, in `agents/` + `pipeline.py`) reads listing sites with Tavily, extracts events with a low-cost model, applies keyword rules, and has an AI curator score each event 0 to 100 with a reason. The team reviews close calls and votes thumbs up or down; votes override the model and become its few-shot examples. The app has three pages: **How it works** (case study: phone hero, system diagram, costs, decisions, plus team controls when signed in), **Ontology of events** (when events happen by day of week, what type they are, and what kind of host puts them on), and **End result** (the list we post, by month, with held and filtered events and why). Readers see a saved snapshot; only signed-in team members trigger paid API calls.

## File map

```
app.py              entry point only: page config, theme, sidebar, team run actions, navigation, page dispatch
ui/theme.py         all app-wide CSS (iframe components keep their own CSS inside their HTML)
ui/components.py    pure render helpers: esc, day_label, site, add_months, checks_html, ai_tag, event_row,
                    filtered_row, sheet_rows, venn_svg. Data in, HTML out, no st calls
ui/data.py          Ctx dataclass + load_ctx(); fetch_live, finish, run_live_search, run_curation, team_password
ui/nav.py           session-state navigation (section + view), the nav buttons; no URL params
ui/sidebar.py       sidebar top (brand, nav slot, team controls, add-event dialog) and bottom (status, sign-in)
ui/hero.py          phone hero component (iframe) and the real Instagram posts in assets/posts/
ui/flow.py          system diagram component (iframe)
ui/howitworks.py    How it works copy and its CSS
ui/story.py         asset helpers (_b64, _font, ASSETS) and the older 7-step story component
views/events.py     End result page: render(ctx)
views/curation.py   How it works page: render(ctx)
views/ontology.py   Ontology page: render(ctx)

agents/, pipeline.py, config.py   the pipeline and settings
filters.py, feedback.py, custom_events.py, kvstore.py, snapshot.py, breaker.py, costs.py, ontology.py
                    core logic and storage (Supabase or local files)
refresh.py          weekly job (GitHub Actions)
tests/              pytest; tests/test_views.py guards the rules below
```

Not used by the app right now: `case_study.py`, `illustrations.py`, `crm/view.py` (Clients page was removed).

## Import rules

- Imports only flow one way: `app -> views -> ui -> core` (core = `agents/`, `config.py`, and the top-level modules listed above).
- A view never imports another view. `ui/` never imports `views/` or `app`.
- No module-level state in `views/` or `ui/`: constants only. Pass data in as arguments or through the `Ctx` object from `ui/data.py`.
- `ui/components.py` stays pure: data in, HTML string out, no `st` calls.
- Keep widget keys and session-state keys stable (`section`, `view`, `team`, `nav-*`, `up-/dn-{key}-{id}`, `collapse-{label}`, `onto-*`). Changing them resets users' state.
- `python -m pytest tests` must pass; `tests/test_views.py` checks the import rules and component purity.

## Rule for agents

One agent per views/ file at a time. Changes to ui/, app.py, or agents/ touch everything and must be done alone. Always work in a worktree on a branch, never on main.
