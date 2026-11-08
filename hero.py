"""The landing hero: a phone scrolling through this week's free picks, Instagram style,
over a soft moving blue background with a giant serif 'seattle' behind it.

If real Instagram post images exist in assets/posts/ (png or jpg), the phone shows
those. Otherwise it shows this week's picks as post cards built from live data.
"""
import base64
import html
import json
from datetime import date

from story import ASSETS, _b64, _font

HEIGHT = 720
POST_COLORS = ["#C9D4F7", "#F5D3E3", "#CFE6F7", "#F6E7C8", "#D9D2F3", "#E3EEDF"]


def _posts_from_files() -> list[str]:
    folder = ASSETS / "posts"
    if not folder.exists():
        return []
    out = []
    for p in sorted(folder.iterdir()):
        mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}.get(p.suffix.lower())
        if mime:
            out.append(f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}")
    return out[:10]


def _when(d) -> str:
    return f"{d:%a} · {d:%b} {d.day}" if isinstance(d, date) else "this week"


def render(events: list[dict]) -> str:
    """events: this week's picks, each {title, date, neighborhood, venue, category}."""
    images = _posts_from_files()
    cards = [{"title": e.get("title", ""), "when": _when(e.get("date")), "hood": e.get("neighborhood") or e.get("venue") or "Seattle",
              "cat": (e.get("category") or "free").lower(), "bg": POST_COLORS[i % len(POST_COLORS)]}
             for i, e in enumerate(events[:8])]
    chips = [f"{c['when'].split(' · ')[0]} · {c['title']}" for c in cards[:3]] or ["free events, every week"]
    fonts = (_font("Bodoni Moda", "bodoni-moda-latin-400-normal.woff2")
             + _font("Bodoni Moda", "bodoni-moda-latin-400-italic.woff2", style="italic")
             + _font("Hanken Grotesk", "hanken-grotesk-latin-400-normal.woff2")
             + _font("Hanken Grotesk", "hanken-grotesk-latin-500-normal.woff2", 500))
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{fonts}
:root{{--ink:#1E2A47;--dim:#4A577D;--serif:'Bodoni Moda',Didot,Georgia,serif;--sans:'Hanken Grotesk',-apple-system,sans-serif}}
*{{box-sizing:border-box;margin:0}}
html,body{{background:transparent;font-family:var(--sans);color:var(--ink)}}
.hero{{position:relative;height:{HEIGHT - 8}px;border-radius:24px;overflow:hidden;background:#DCE6F3}}
.blob{{position:absolute;border-radius:50%;filter:blur(60px);opacity:.95}}
.b1{{width:520px;height:420px;left:-120px;top:-80px;background:#C3CEF5;animation:d1 18s ease-in-out infinite alternate}}
.b2{{width:480px;height:420px;right:-100px;top:120px;background:#F4CFDF;animation:d2 22s ease-in-out infinite alternate}}
.b3{{width:560px;height:360px;left:28%;bottom:-160px;background:#BFE0F7;animation:d3 20s ease-in-out infinite alternate}}
@keyframes d1{{to{{transform:translate(120px,80px) scale(1.1)}}}}
@keyframes d2{{to{{transform:translate(-140px,-60px) scale(.95)}}}}
@keyframes d3{{to{{transform:translate(-80px,-60px) scale(1.15)}}}}
.grain{{position:absolute;inset:0;opacity:.18;mix-blend-mode:multiply;
  background-image:radial-gradient(rgba(30,42,71,.18) 1px,transparent 1px);background-size:3px 3px}}
.bar{{position:absolute;left:0;right:0;top:0;display:grid;grid-template-columns:1fr auto 1fr;align-items:center;padding:22px 34px;font-size:15px;z-index:5}}
.bar b{{font:400 19px var(--serif);letter-spacing:.16em}}
.bar a{{justify-self:end;color:var(--ink);text-decoration:none;border-bottom:1px solid rgba(30,42,71,.4);padding-bottom:1px;transition:border-color .3s}}
.bar a:hover{{border-color:var(--ink)}}
.giant{{position:absolute;left:50%;top:104px;transform:translateX(-50%);font:400 clamp(150px,21vw,300px)/.8 var(--serif);
  letter-spacing:-.03em;white-space:nowrap;color:var(--ink);z-index:1;pointer-events:none}}
.giant i{{font-style:italic}}
.stage{{position:absolute;inset:0;perspective:1600px;z-index:3}}
.phone{{position:absolute;left:50%;top:92px;width:300px;height:600px;margin-left:-150px;border-radius:46px;background:#14182A;padding:11px;
  box-shadow:0 50px 100px rgba(20,30,70,.35),inset 0 0 0 1.5px #3A4160;transform-style:preserve-3d;
  transition:transform .7s cubic-bezier(.2,.8,.2,1)}}
.screen{{position:relative;width:100%;height:100%;border-radius:36px;overflow:hidden;background:#fff}}
.notch{{position:absolute;left:50%;top:9px;width:92px;height:26px;margin-left:-46px;border-radius:20px;background:#14182A;z-index:4}}
.ig{{position:absolute;left:0;right:0;top:0;height:86px;padding:44px 14px 0;display:flex;align-items:center;gap:9px;background:#fff;z-index:3;
  border-bottom:1px solid #EEF0F5}}
.av{{width:30px;height:30px;border-radius:50%;padding:2px;background:conic-gradient(#F2A7C3,#B7A6F2,#9CC7F2,#F2A7C3)}}
.av i{{display:grid;place-items:center;width:100%;height:100%;border-radius:50%;background:#fff;font:italic 400 13px var(--serif);border:2px solid #fff}}
.ig b{{font-weight:500;font-size:13.5px}}
.ig span{{margin-left:auto;font-size:12px;color:#fff;background:#5469C4;border-radius:8px;padding:5px 11px}}
.feed{{position:absolute;left:0;right:0;top:86px;animation:scroll 28s linear infinite}}
.screen:hover .feed{{animation-play-state:paused}}
@keyframes scroll{{to{{transform:translateY(-50%)}}}}
.post{{padding:0 0 12px}}
.sq{{aspect-ratio:1/1;position:relative;display:flex;flex-direction:column;justify-content:space-between;padding:18px 16px;overflow:hidden}}
.sq img{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}}
.sq .k{{font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--dim)}}
.sq h4{{font:400 26px/1.02 var(--serif);color:var(--ink);text-wrap:balance}}
.sq .row{{display:flex;justify-content:space-between;align-items:flex-end;font-size:11.5px;color:var(--dim)}}
.sq .free{{font:italic 400 15px var(--serif);background:#fff;color:var(--ink);padding:3px 10px;border-radius:999px}}
.act{{display:flex;gap:12px;padding:9px 14px 2px;font-size:16px;color:var(--ink)}}
.cap{{padding:2px 14px;font-size:11.5px;line-height:1.4;color:#3B4363}}
.cap b{{font-weight:500}}
.chip{{position:absolute;z-index:4;background:rgba(255,255,255,.82);backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,.9);
  border-radius:999px;padding:9px 16px;font-size:14px;box-shadow:0 12px 30px rgba(30,50,110,.14);white-space:nowrap;
  transition:transform .8s cubic-bezier(.2,.8,.2,1);animation:bob 6s ease-in-out infinite}}
.chip i{{font-family:var(--serif)}}
.c1{{left:9%;top:42%}}.c2{{right:8%;top:30%;animation-delay:-2s}}.c3{{right:13%;bottom:15%;animation-delay:-4s}}
@keyframes bob{{50%{{margin-top:-8px}}}}
.foot{{position:absolute;left:34px;right:34px;bottom:24px;display:flex;justify-content:space-between;font-size:15px;z-index:5;color:var(--dim)}}
.foot b{{font:italic 400 19px var(--serif);color:var(--ink)}}
@media (max-width:760px){{.giant{{font-size:110px;top:120px}}.chip{{display:none}}.bar{{padding:18px}}.bar span{{display:none}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important;transition:none!important}}}}
</style></head><body>
<div class="hero" id="hero">
  <div class="blob b1"></div><div class="blob b2"></div><div class="blob b3"></div><div class="grain"></div>
  <div class="bar"><span>free things to do, every week</span><b>SEATTLE UNLOCKED</b>
    <a href="https://www.instagram.com/seattle_forfree/" target="_blank" rel="noopener">@seattle_forfree</a></div>
  <div class="giant">seat<i>tle</i></div>
  <div class="stage" id="stage">
    <div class="phone" id="phone"><div class="screen"><div class="notch"></div>
      <div class="ig"><div class="av"><i>su</i></div><b>seattle_forfree</b><span>Follow</span></div>
      <div class="feed" id="feed"></div></div></div>
    {''.join(f'<div class="chip c{i + 1}" data-d="{(i + 1) * 9}">{html.escape(c)}</div>' for i, c in enumerate(chips))}
  </div>
  <div class="foot"><span><b>free</b> &nbsp;no tickets, no sales pitches</span><span>picked by people who live here</span></div>
</div>
<script>
const IMGS = {json.dumps(images)}, CARDS = {json.dumps(cards)};
const feed = document.getElementById('feed');
function post(inner, cap) {{
  const p = document.createElement('div'); p.className = 'post';
  p.innerHTML = '<div class="sq"></div><div class="act">♡ &nbsp;◯ &nbsp;➤</div><div class="cap"><b>seattle_forfree</b> </div>';
  p.querySelector('.sq').appendChild(inner); p.querySelector('.cap').appendChild(document.createTextNode(cap)); return p;
}}
function build() {{
  const items = [];
  if (IMGS.length) IMGS.forEach(src => {{ const im = new Image(); im.src = src; im.alt = 'Seattle Unlocked post';
    items.push(post(im, 'free this week. see you there')); }});
  else CARDS.forEach(c => {{
    const f = document.createDocumentFragment(), d = document.createElement('div');
    d.style.cssText = 'display:contents';
    d.innerHTML = '<span class="k"></span><h4></h4><div class="row"><span class="w"></span><span class="free">free</span></div>';
    d.querySelector('.k').textContent = c.cat; d.querySelector('h4').textContent = c.title;
    d.querySelector('.w').textContent = c.when + ' · ' + c.hood;
    const p = post(d, c.hood.toLowerCase() + ', this one is for you');
    p.querySelector('.sq').style.background = c.bg; items.push(p);
  }});
  [...items, ...items.map(n => n.cloneNode(true))].forEach(n => feed.appendChild(n));  // two copies for a seamless loop
}}
build();
const hero = document.getElementById('hero'), phone = document.getElementById('phone'), chips = [...document.querySelectorAll('.chip')];
hero.addEventListener('mousemove', e => {{
  const b = hero.getBoundingClientRect(), x = (e.clientX - b.left) / b.width - .5, y = (e.clientY - b.top) / b.height - .5;
  phone.style.transform = `rotateY(${{x * 12}}deg) rotateX(${{-y * 8}}deg)`;
  chips.forEach(c => {{ const d = +c.dataset.d; c.style.transform = `translate(${{x * d}}px, ${{y * d}}px)`; }});
}});
hero.addEventListener('mouseleave', () => {{ phone.style.transform = ''; chips.forEach(c => c.style.transform = ''); }});
</script></body></html>"""
