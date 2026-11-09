"""The page split: every view imports cleanly, components stay pure, and imports flow one way."""
import ast
import importlib
import pathlib
from datetime import date

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent


def sample_row(**over) -> pd.Series:
    row = {"title": "First Thursday Art Walk", "link": "https://example.com/art", "category": "Art", "status": "Pick",
           "custom": False, "ai_score": 91, "ai_intent": "Arts and culture", "ai_reason": "Open to everyone.",
           "key": "firstthursdayartwalk|2026-11-05", "venue": "Pioneer Square galleries", "neighborhood": "Pioneer Square",
           "time": "5pm", "cost": "Free", "site": "everout.com", "checks": [], "date": date(2026, 11, 5)}
    row.update(over)
    return pd.Series(row)


def test_each_view_imports_and_exposes_render():
    for name in ("events", "curation", "ontology", "press"):
        mod = importlib.import_module(f"views.{name}")
        assert callable(mod.render), name


def test_event_row_renders_a_sample_event():
    from ui.components import event_row
    html = event_row(1, sample_row(), votes={"firstthursdayartwalk|2026-11-05": 1})
    assert "First Thursday Art Walk" in html and "https://example.com/art" in html
    assert "AI 91" in html and "team ▲" in html and "Pioneer Square galleries" in html
    held = event_row(2, sample_row(checks=[{"check": "Date", "passed": False, "detail": "no date"}]), held=True)
    assert "✕ Date" in held and "no date" in held and "team ▲" not in held


def _imports(path: pathlib.Path) -> set[str]:
    out = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            out |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.add(node.module)
            if node.module in ("views", "ui"):
                out |= {f"{node.module}.{a.name}" for a in node.names}
    return out


def test_imports_flow_one_way():
    # app -> views -> ui -> core. A view never imports another view; ui never imports views.
    for p in (ROOT / "views").glob("*.py"):
        bad = {m for m in _imports(p) if m == "views" or m.startswith("views.")}
        assert not bad, f"{p.name} imports a view: {bad}"
    for p in (ROOT / "ui").glob("*.py"):
        bad = {m for m in _imports(p) if m == "views" or m.startswith("views.") or m == "app"}
        assert not bad, f"ui/{p.name} imports {bad}"


def test_components_are_pure():
    src = (ROOT / "ui" / "components.py").read_text()
    assert "import streamlit" not in src and "st." not in src


def test_ontology_profile_counts_days_types_and_hosts():
    import ontology
    assert ontology.host_type("Seattle Public Library, Central") == "Libraries"
    assert ontology.host_type("Flying Lion Brewing") == "Bars, cafes & restaurants"
    assert ontology.host_type("", "Mystery night") == ontology.UNSURE
    trace = [{"title": "Jazz night", "venue": "The Triple Door", "date": date(2026, 11, 7), "status": "Pick",
              "category": "Music"},
             {"title": "Jazz night", "venue": "The Triple Door", "date": date(2026, 11, 7), "status": "Duplicate",
              "category": "Music"},
             {"title": "Paid gala", "venue": "Hotel Andra", "date": date(2026, 11, 9), "status": "Filtered",
              "category": "Community"}]
    p = ontology.profile(trace)
    assert p["n"] == 1 and p["days"]["Sat"] == 1 and p["kinds"]["Music"] == 1
    assert p["hosts"]["Music & theater venues"] == 1 and p["day_kind"][("Music", "Sat")] == 1
    assert ontology.profile(trace, live_only=False)["hosts"]["Hotels"] == 1


def test_press_logo_falls_back_to_name():
    from views import press
    assert press.slug("The Westin") == "the-westin" and press.slug("KING 5") == "king-5"
    assert press.logo("Nobody Inc") == "Nobody Inc"
    assert "105+" in press.clients_html() and "NPR" in press.featured_html(press.PRESS_OUTLETS)


def test_press_logos_load_with_balanced_size():
    from views import press
    img = press.logo("Tinder")
    assert img.startswith("<img") and "height:" in img
