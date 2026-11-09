"""Press and clients: who has worked with Seattle Unlocked, and where we've been featured."""
import base64
import json
import re
import struct

import streamlit as st

from config import PROJECT_DIR
from ui.components import esc

CLIENT_COUNT = "105+"
# The big names get logo tiles. Drop a logo into assets/logos/ named by slug (tinder.png, the-westin.svg, ...).
FEATURED = ["Tinder", "Seattle Sounders", "City of Seattle", "The Westin", "CBRE", "Downtown Seattle Association"]
CLIENTS = [
    "Junction FC", "aT Center LA", "Clockout", "Great Big Game Show", "Short Run Comix Festival", "Keiro Northwest",
    "Baila District", "MUZ Fest Seattle", "Formosound", "Juice Time", "Goldvine Coffee",
]
PRESS_OUTLETS = ["KING 5", "VoyageLA", "NPR"]
LOGOS = PROJECT_DIR / "assets" / "logos"
PRESS_FILE = PROJECT_DIR / "assets" / "press.json"   # [{"outlet": "...", "title": "...", "url": "...", "date": "..."}]
MIME = {".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}

CSS = """<style>
.pc-k{font-size:12px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#5469C4;margin:0 0 6px}
.pc-h{font-family:'Bodoni Moda',Didot,Georgia,serif;font-style:italic;font-size:30px;color:#1E2A47;margin:0 0 6px;line-height:1.2}
.pc-h b{font-family:'Bodoni Moda',Didot,Georgia,serif;font-style:normal;font-weight:400;color:#5469C4}
.pc-sub{font-size:15px;color:var(--dim);margin:0 0 22px;max-width:60ch;line-height:1.5}
.pc-wall{display:grid;background:#fff;border:1px solid var(--line);border-radius:14px;overflow:hidden}
.pc-wall div{background:#fff;display:flex;align-items:center;justify-content:center;text-align:center;
             box-shadow:0 0 0 .5px var(--line);color:#1E2A47;letter-spacing:-.01em;transition:background .2s,color .2s}
.pc-wall div:hover{background:#F3F5FC;color:#5469C4}
.pc-big{grid-template-columns:repeat(auto-fill,minmax(250px,1fr));margin-bottom:14px}
.pc-big div{min-height:132px;padding:22px 26px;font-size:21px;font-weight:700}
.pc-big div{min-height:150px}
.pc-big img{max-width:72%;object-fit:contain;transition:transform .25s}
.pc-big div:hover{background:#fff}
.pc-big div:hover img{transform:scale(1.05)}
.pc-small{display:flex;flex-wrap:wrap;gap:10px;background:none;border:none;border-radius:0;overflow:visible;margin-bottom:14px}
.pc-small div{padding:10px 18px;border:1px solid var(--line);border-radius:999px;box-shadow:none;font-size:15px;font-weight:600}
.pc-more{font-size:14px;color:var(--dim);margin:0 0 48px}
.pc-feat{display:flex;flex-wrap:wrap;align-items:center;gap:14px 56px;padding:26px 30px;background:#fff;
         border:1px solid var(--line);border-radius:14px;margin-bottom:40px}
.pc-feat span{font-size:28px;font-weight:700;color:#1E2A47;letter-spacing:-.02em;opacity:.8}
.pc-feat img{max-height:44px;max-width:160px;object-fit:contain;filter:grayscale(1);opacity:.85}
.pc-press a{display:grid;grid-template-columns:150px 1fr auto;gap:16px;align-items:baseline;padding:16px 4px;
            border-top:1px solid var(--line);text-decoration:none;color:#1E2A47}
.pc-press a:last-child{border-bottom:1px solid var(--line)}
.pc-press a:hover b{color:#5469C4}
.pc-press span{font-size:12px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--dim)}
.pc-press b{font-size:16px;font-weight:600}
.pc-press i{font-style:normal;font-size:13px;color:var(--dim)}
@media (max-width:640px){.pc-press a{grid-template-columns:1fr}.pc-feat{gap:14px 32px}.pc-feat span{font-size:22px}}
</style>"""


def render(ctx) -> None:
    st.markdown("<div class='ob ob-title'><h1>Press and clients</h1>"
                "<p>Brands, the city, and local favorites reach Seattle through us.</p></div>",
                unsafe_allow_html=True)
    st.markdown(CSS + clients_html() + featured_html(PRESS_OUTLETS) + press_html(load_press()),
                unsafe_allow_html=True)


def load_press() -> list[dict]:
    try:
        return json.loads(PRESS_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def logo(name: str) -> str:
    """An <img> for assets/logos/<slug>.*, or the name in type when there's no logo file yet."""
    for ext, mime in MIME.items():
        path = LOGOS / f"{slug(name)}{ext}"
        if path.exists():
            raw = path.read_bytes()
            data = base64.b64encode(raw).decode()
            return f"<img src='data:{mime};base64,{data}' alt='{esc(name)}'{size(raw)}>"
    return esc(name)


def size(raw: bytes) -> str:
    """Give every logo about the same visual weight: wide wordmarks shorter, tall crests taller."""
    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        return ""
    w, h = struct.unpack(">II", raw[16:24])
    return f" style='height:{min(max((7000 * h / w) ** .5, 34), 96):.0f}px'"


def clients_html() -> str:
    return (f"<div class='pc-k'>Clients</div><div class='pc-h'>Partnered with <b>{CLIENT_COUNT}</b> clients</div>"
            "<div class='pc-sub'>From global brands to the corner coffee shop.</div>"
            "<div class='pc-wall pc-big'>" + "".join(f"<div>{logo(c)}</div>" for c in FEATURED) + "</div>"
            "<div class='pc-wall pc-small'>" + "".join(f"<div>{esc(c)}</div>" for c in CLIENTS) + "</div>"
            "<div class='pc-more'>and many more across Seattle.</div>")


def featured_html(outlets: list[str]) -> str:
    items = "".join(m if m.startswith("<img") else f"<span>{m}</span>" for m in map(logo, outlets))
    return f"<div class='pc-k'>Press</div><div class='pc-h'>As featured on</div><div class='pc-feat'>{items}</div>"


def press_html(items: list[dict]) -> str:
    """Individual stories, hidden until assets/press.json has some."""
    if not items:
        return ""
    rows = "".join(
        f"<a href='{esc(p.get('url', '#'))}' target='_blank' rel='noopener'><span>{esc(p.get('outlet', ''))}</span>"
        f"<b>{esc(p.get('title', ''))}</b><i>{esc(p.get('date', ''))}</i></a>" for p in items)
    return f"<div class='pc-press'>{rows}</div>"
