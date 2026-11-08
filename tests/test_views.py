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
    for name in ("events", "curation", "ontology"):
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
