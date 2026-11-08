"""'How a pick is made': the seven-step story at the top of the AI curation page.

Editorial layout in soft blue: a giant serif step number and an italic title on the
left, the real app screen in a frosted-glass frame on the right, and a hairline list
of all seven steps underneath. Hovering (or tapping) a step swaps the story; the
screen tilts gently toward the mouse.

Rendered with streamlit.components.v1.html, so it's one self-contained document:
fonts and screenshots are inlined from assets/.
"""
import base64
import html
import json
from functools import lru_cache

from config import PROJECT_DIR

ASSETS = PROJECT_DIR / "assets"
HEIGHT = 900


@lru_cache(maxsize=None)
def _b64(path: str) -> str:
    return base64.b64encode((ASSETS / path).read_bytes()).decode()


def _font(family: str, file: str, weight: int = 400, style: str = "normal") -> str:
    return (f"@font-face{{font-family:'{family}';font-weight:{weight};font-style:{style};font-display:block;"
            f"src:url(data:font/woff2;base64,{_b64('fonts/' + file)}) format('woff2')}}")


def render(steps: list[dict]) -> str:
    """steps: [{title, text, stats: [(number, label)], image: 'steps/s1.png' | None, quiet: str | None}]"""
    fonts = (_font("Bodoni Moda", "bodoni-moda-latin-400-normal.woff2")
             + _font("Bodoni Moda", "bodoni-moda-latin-400-italic.woff2", style="italic")
             + _font("Hanken Grotesk", "hanken-grotesk-latin-400-normal.woff2")
             + _font("Hanken Grotesk", "hanken-grotesk-latin-500-normal.woff2", 500))
    data = [{"n": f"{i + 1:02d}", "title": s["title"], "text": s["text"],
             "stats": [[str(a), b] for a, b in s.get("stats", [])],
             "img": f"data:image/png;base64,{_b64(s['image'])}" if s.get("image") else "",
             "quiet": s.get("quiet") or ""} for i, s in enumerate(steps)]
    rows = "".join(
        f"<button class='row' data-i='{i}' type='button'><i>{d['n']}</i><span class='rt'>{html.escape(d['title'])}</span>"
        f"<span class='rm'>{html.escape(' · '.join(f'{a} {b}' for a, b in d['stats'][:1]))}</span>"
        f"<span class='ar' aria-hidden='true'>→</span></button>"
        for i, d in enumerate(data))
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{fonts}
/* Look: Botanica's editorial serif + a frosted product screen, in soft Seattle blue with a blush glow. */
:root{{--bg:#E0E9F5;--ink:#1E2A47;--dim:#45527A;--hair:rgba(30,42,71,.32);--hover:#D3DFF0;
  --blush:#F2CFE0;--peri:#C7D1F6;--serif:'Bodoni Moda',Didot,Georgia,serif;--sans:'Hanken Grotesk',-apple-system,sans-serif}}
*{{box-sizing:border-box;margin:0}}
html,body{{background:transparent}}
body{{font-family:var(--sans);color:var(--ink)}}
.wrap{{background:var(--bg);border-radius:20px;overflow:hidden;position:relative;height:{HEIGHT - 8}px;display:flex;flex-direction:column}}
.bar{{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;padding:20px 32px;border-bottom:1px solid var(--hair);font-size:15px}}
.bar b{{font:400 19px var(--serif);letter-spacing:.14em}}
.bar span:last-child{{text-align:right;color:var(--dim)}}
.stage{{flex:1;display:grid;grid-template-columns:minmax(0,.82fr) minmax(0,1.18fr);gap:28px;padding:10px 32px 24px;position:relative;min-height:0}}
.glow{{position:absolute;border-radius:50%;filter:blur(70px);pointer-events:none;transition:transform 1.2s ease}}
.g1{{width:46%;height:70%;right:4%;top:14%;background:var(--blush);opacity:.9}}
.g2{{width:30%;height:44%;right:-4%;top:-10%;background:var(--peri)}}
.left{{position:relative;display:flex;flex-direction:column;justify-content:flex-end;min-width:0}}
.num{{font:400 clamp(150px,19vw,236px)/.82 var(--serif);letter-spacing:-.03em;margin-bottom:auto;padding-top:6px}}
h2{{font:italic 400 clamp(30px,3.4vw,42px)/1.05 var(--serif);margin:8px 0 12px;text-wrap:balance}}
.text{{font-size:16.5px;line-height:1.55;color:var(--dim);max-width:40ch}}
.stats{{display:flex;gap:30px;margin-top:18px;min-height:64px}}
.stats div{{font-size:14px;color:var(--dim)}}
.stats b{{display:block;font:400 34px/1.1 var(--serif);color:var(--ink)}}
.right{{position:relative;display:flex;align-items:center;perspective:1400px;min-width:0}}
.glass{{position:relative;width:100%;aspect-ratio:16/10.4;border-radius:18px;padding:14px;
  background:linear-gradient(135deg,rgba(255,255,255,.62),rgba(255,255,255,.22));border:1px solid rgba(255,255,255,.75);
  box-shadow:0 40px 90px rgba(30,50,110,.20);transform-style:preserve-3d;transition:transform .6s cubic-bezier(.2,.8,.2,1)}}
.screen{{position:absolute;inset:14px;border-radius:10px;overflow:hidden;background:#FBF9F7}}
.screen img{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:left top;opacity:0;
  transform:scale(1.02);transition:opacity .45s ease,transform .7s ease}}
.screen img.on{{opacity:1;transform:none}}
.quiet{{position:absolute;inset:0;display:grid;place-items:center;text-align:center;padding:30px;opacity:0;transition:opacity .45s;
  background:linear-gradient(160deg,#F4F7FC,#EEF1FA)}}
.quiet.on{{opacity:1}}
.quiet p{{font:italic 400 clamp(26px,3vw,40px)/1.15 var(--serif);max-width:16ch}}
.quiet small{{display:block;font:400 14px var(--sans);color:var(--dim);margin-top:14px;letter-spacing:.02em}}
.list{{border-top:1px solid var(--hair)}}
.row{{all:unset;box-sizing:border-box;width:100%;cursor:pointer;display:grid;grid-template-columns:60px minmax(0,1fr) auto 34px;
  align-items:center;padding:12px 32px;border-bottom:1px solid var(--hair);font-size:16.5px;transition:padding .35s cubic-bezier(.2,.8,.2,1),background .25s}}
.row:last-child{{border-bottom:none}}
.row i{{font:italic 400 20px var(--serif)}}
.row .rm{{font-size:14px;color:var(--dim)}}
.row .ar{{text-align:right;transition:transform .35s cubic-bezier(.2,.8,.2,1)}}
.row:hover,.row.on{{background:var(--hover);padding-left:44px}}
.row:hover .ar,.row.on .ar{{transform:translateX(6px)}}
.row:focus-visible{{outline:2px solid var(--ink);outline-offset:-2px}}
.fade{{transition:opacity .3s ease,transform .45s cubic-bezier(.2,.8,.2,1)}}
.fade.out{{opacity:0;transform:translateY(8px)}}
@media (max-width:760px){{.stage{{grid-template-columns:1fr}}.num{{font-size:120px}}.right{{display:none}}
  .row{{grid-template-columns:44px minmax(0,1fr) 24px;padding:12px 18px}}.row .rm{{display:none}}.bar{{padding:16px 18px}}}}
@media (prefers-reduced-motion:reduce){{*{{transition:none!important}}}}
</style></head><body>
<div class="wrap">
  <div class="bar"><span>how a pick gets made</span><b>SEATTLE UNLOCKED</b><span>@seattle_forfree</span></div>
  <div class="stage" id="stage">
    <div class="glow g1" id="g1"></div><div class="glow g2" id="g2"></div>
    <div class="left fade" id="left"><div class="num" id="num"></div><h2 id="title"></h2><p class="text" id="text"></p>
      <div class="stats" id="stats"></div></div>
    <div class="right"><div class="glass" id="glass"><div class="screen" id="screen"></div></div></div>
  </div>
  <div class="list" id="list">{rows}</div>
</div>
<script>
const D = {json.dumps(data)};
const $ = id => document.getElementById(id);
const screen = $('screen');
D.forEach((d, i) => {{
  if (d.img) {{ const im = new Image(); im.src = d.img; im.alt = d.title; im.dataset.i = i; screen.appendChild(im); }}
  else {{ const q = document.createElement('div'); q.className = 'quiet'; q.dataset.i = i;
         q.innerHTML = '<div><p></p><small></small></div>'; q.querySelector('p').textContent = d.quiet;
         q.querySelector('small').textContent = d.title; screen.appendChild(q); }}
}});
const rows = [...document.querySelectorAll('.row')];
let cur = -1;
function show(i) {{
  if (i === cur) return; cur = i; const d = D[i];
  rows.forEach((r, k) => r.classList.toggle('on', k === i));
  [...screen.children].forEach(el => el.classList.toggle('on', +el.dataset.i === i));
  const left = $('left'); left.classList.add('out');
  setTimeout(() => {{
    $('num').textContent = d.n; $('title').textContent = d.title; $('text').textContent = d.text;
    $('stats').innerHTML = d.stats.map(s => '<div><b></b></div>').join('');
    [...$('stats').children].forEach((el, k) => {{ el.querySelector('b').textContent = d.stats[k][0];
      el.appendChild(document.createTextNode(d.stats[k][1])); }});
    left.classList.remove('out');
  }}, 160);
  $('g1').style.transform = `translate(${{(i % 3 - 1) * 30}}px, ${{(i % 2) * 24}}px)`;
}}
rows.forEach((r, i) => {{ r.addEventListener('mouseenter', () => show(i)); r.addEventListener('focus', () => show(i));
  r.addEventListener('click', () => show(i)); }});
const stage = $('stage'), glass = $('glass');
stage.addEventListener('mousemove', e => {{
  const b = stage.getBoundingClientRect(), x = (e.clientX - b.left) / b.width - .5, y = (e.clientY - b.top) / b.height - .5;
  glass.style.transform = `rotateY(${{x * 7}}deg) rotateX(${{-y * 5}}deg) translateZ(0)`;
}});
stage.addEventListener('mouseleave', () => glass.style.transform = '');
show(0);
</script></body></html>"""
