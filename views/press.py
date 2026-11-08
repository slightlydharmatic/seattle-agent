"""Press and clients: who has worked with Seattle Unlocked, and where we've been written up."""
import json

import streamlit as st

from config import PROJECT_DIR
from ui.components import esc

# Order matters: the first row is what people see first.
CLIENTS = [
    "Tinder", "Seattle Sounders", "City of Seattle", "The Westin", "CBRE", "Downtown Seattle Association",
    "Junction FC", "aT Center LA", "Clockout", "Great Big Game Show", "Short Run Comix Festival", "Keiro Northwest", "Baila District",
    "MUZ Fest Seattle", "Formosound", "Juice Time", "Goldvine Coffee",
]
PRESS_FILE = PROJECT_DIR / "assets" / "press.json"   # [{"outlet": "...", "title": "...", "url": "...", "date": "..."}]

CSS = """<style>
.pc-k{font-size:12px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#5469C4;margin:0 0 6px}
.pc-h{font-family:'Bodoni Moda',Didot,Georgia,serif;font-style:italic;font-size:30px;color:#1E2A47;margin:0 0 6px;line-height:1.2}
.pc-sub{font-size:15px;color:var(--dim);margin:0 0 22px;max-width:60ch;line-height:1.5}
.pc-wall{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));background:#fff;
         border:1px solid var(--line);border-radius:14px;overflow:hidden;margin-bottom:40px}
.pc-wall div{background:#fff;min-height:96px;display:flex;align-items:center;justify-content:center;text-align:center;
             padding:14px 16px;box-shadow:0 0 0 .5px var(--line);font-size:17px;font-weight:600;color:#1E2A47;letter-spacing:-.01em;transition:background .2s,color .2s}
.pc-wall div:hover{background:#F3F5FC;color:#5469C4}
.pc-press a{display:grid;grid-template-columns:150px 1fr auto;gap:16px;align-items:baseline;padding:16px 4px;
            border-top:1px solid var(--line);text-decoration:none;color:#1E2A47}
.pc-press a:last-child{border-bottom:1px solid var(--line)}
.pc-press a:hover b{color:#5469C4}
.pc-press span{font-size:12px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--dim)}
.pc-press b{font-size:16px;font-weight:600}
.pc-press i{font-style:normal;font-size:13px;color:var(--dim)}
@media (max-width:640px){.pc-press a{grid-template-columns:1fr}}
</style>"""


def render(ctx) -> None:
    st.markdown("<div class='ob ob-title'><h1>Press and clients</h1>"
                "<p>Brands, the city, and local favorites reach Seattle through us.</p></div>",
                unsafe_allow_html=True)
    st.markdown(CSS + clients_html(CLIENTS) + press_html(load_press()), unsafe_allow_html=True)


def load_press() -> list[dict]:
    try:
        return json.loads(PRESS_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def clients_html(clients: list[str]) -> str:
    return ("<div class='pc-k'>Clients</div><div class='pc-h'>Who we've worked with</div>"
            f"<div class='pc-sub'>{len(clients)} partners, from global brands to the corner coffee shop.</div>"
            "<div class='pc-wall'>" + "".join(f"<div>{esc(c)}</div>" for c in clients) + "</div>")


def press_html(items: list[dict]) -> str:
    """Hidden until there's real press to show."""
    if not items:
        return ""
    rows = "".join(
        f"<a href='{esc(p.get('url', '#'))}' target='_blank' rel='noopener'><span>{esc(p.get('outlet', ''))}</span>"
        f"<b>{esc(p.get('title', ''))}</b><i>{esc(p.get('date', ''))}</i></a>" for p in items)
    return f"<div class='pc-k'>Press</div><div class='pc-h'>In the news</div><div class='pc-press'>{rows}</div>"
