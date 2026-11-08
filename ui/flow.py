"""The system diagram on the How it works page.

Three lanes (agent, guardrails, people) on one grid, arrows drawn from the real
node positions, and a feedback loop from the team back into the curator.
Hovering a node shows what it does, what it costs, and a real screen when we have one.
"""
import json

from ui.story import _b64, _font

HEIGHT = 640


def render(nodes: list[dict], edges: list[tuple], loops: list[tuple]) -> str:
    """nodes: {id, col, row, lane, title, sub, tag, cost?, img?}; edges/loops: (from_id, to_id, label?)."""
    for n in nodes:
        if n.get("img"):
            n["img"] = f"data:image/png;base64,{_b64(n['img'])}"
    fonts = (_font("Bodoni Moda", "bodoni-moda-latin-400-normal.woff2")
             + _font("Bodoni Moda", "bodoni-moda-latin-400-italic.woff2", style="italic")
             + _font("Hanken Grotesk", "hanken-grotesk-latin-400-normal.woff2")
             + _font("Hanken Grotesk", "hanken-grotesk-latin-500-normal.woff2", 500))
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{fonts}
:root{{--ink:#1E2A47;--dim:#4A577D;--soft:#7A84A3;--line:#C9D3E6;--bg:#F4F7FC;--card:#fff;--peri:#5469C4;--rose:#B5658A;
  --serif:'Bodoni Moda',Didot,Georgia,serif;--sans:'Hanken Grotesk',-apple-system,sans-serif;--mono:ui-monospace,'SF Mono',Menlo,monospace}}
*{{box-sizing:border-box;margin:0}}
html,body{{background:transparent;font-family:var(--sans);color:var(--ink)}}
.wrap{{position:relative;background:var(--bg);border-radius:20px;padding:22px 22px 18px;height:{HEIGHT - 8}px;overflow:hidden;
  background-image:radial-gradient(rgba(30,42,71,.09) 1px,transparent 1px);background-size:18px 18px}}
.lanes{{position:absolute;left:22px;top:22px;bottom:46px;width:86px;display:grid;grid-template-rows:1.25fr 1fr 1fr;pointer-events:none}}
.lanes div{{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--soft);padding-top:8px}}
.grid{{position:absolute;left:108px;right:22px;top:22px;bottom:46px;display:grid;grid-template-columns:repeat(6,minmax(0,1fr));
  grid-template-rows:1.25fr 1fr 1fr;gap:18px 22px}}
.node{{position:relative;z-index:2;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:11px 12px;
  display:flex;flex-direction:column;gap:4px;align-self:center;cursor:default;
  transition:transform .3s cubic-bezier(.2,.8,.2,1),box-shadow .3s,border-color .3s}}
.node:hover,.node.hot{{transform:translateY(-3px);box-shadow:0 16px 34px rgba(30,50,110,.14);border-color:var(--ink)}}
.node.guard{{border-style:dashed;border-color:#9DAAE0;background:#F9FAFF}}
.node.human{{background:#FDF6F9;border-color:#E6C3D3}}
.node .n{{font-size:10.5px;color:var(--soft);letter-spacing:.06em}}
.node b{{font:400 18px/1.1 var(--serif)}}
.node p{{font-size:12px;line-height:1.35;color:var(--dim)}}
.tag{{align-self:flex-start;font:500 10.5px var(--mono);padding:3px 7px;border-radius:6px;background:#EEF1FA;color:var(--ink);margin-top:2px}}
.tag.cheap{{background:#E6F2EC;color:#2F6B53}}.tag.strong{{background:#EEE9FB;color:#4B3FA6}}.tag.free{{background:#F1F1F1;color:#555}}
.tag.ppl{{background:#F8E3EC;color:#8A3E62}}
.band{{display:flex;gap:4px;margin-top:3px}}
.band span{{flex:1;font:500 10px var(--mono);text-align:center;padding:4px 0;border-radius:5px}}
svg{{position:absolute;inset:0;width:100%;height:100%;z-index:1;pointer-events:none;overflow:visible}}
.lbl{{font:500 10.5px var(--sans);fill:var(--rose)}}
.legend{{position:absolute;left:108px;right:22px;bottom:14px;display:flex;gap:18px;flex-wrap:wrap;font-size:11.5px;color:var(--soft)}}
.legend i{{display:inline-block;width:20px;height:0;border-top:1.5px solid var(--ink);vertical-align:middle;margin-right:6px}}
.legend .lp i{{border-top:1.5px dashed var(--rose)}}
.peek{{position:absolute;z-index:5;width:320px;background:#fff;border-radius:14px;box-shadow:0 24px 60px rgba(20,30,70,.22);
  padding:12px;opacity:0;transform:translateY(6px);transition:opacity .2s,transform .25s;pointer-events:none}}
.peek.on{{opacity:1;transform:none}}
.peek img{{width:100%;border-radius:8px;display:block;margin-bottom:9px;border:1px solid #EEF0F5}}
.peek b{{font:400 18px var(--serif);display:block;margin-bottom:4px}}
.peek p{{font-size:12.5px;line-height:1.45;color:var(--dim)}}
.peek .c{{font:500 11px var(--mono);color:var(--ink);margin-top:7px;display:block}}
@media (prefers-reduced-motion:reduce){{*{{transition:none!important}}}}
</style></head><body>
<div class="wrap" id="wrap">
  <div class="lanes"><div>Agent</div><div>Guardrails</div><div>People</div></div>
  <div class="grid" id="grid"></div>
  <svg id="svg"><defs>
    <marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10z" fill="#1E2A47"/></marker>
    <marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10z" fill="#B5658A"/></marker>
  </defs></svg>
  <div class="legend"><span><i></i>data flow</span><span class="lp"><i></i>feedback loop</span>
    <span>green tag = low-cost model · purple = judgment model · grey = no model</span><span>hover any step</span></div>
  <div class="peek" id="peek"></div>
</div>
<script>
const N = {json.dumps(nodes)}, E = {json.dumps(edges)}, L = {json.dumps(loops)};
const grid = document.getElementById('grid'), svg = document.getElementById('svg'), wrap = document.getElementById('wrap'), peek = document.getElementById('peek');
const el = {{}};
N.forEach((n, i) => {{
  const d = document.createElement('div'); d.className = 'node ' + (n.lane || ''); d.id = 'n-' + n.id;
  d.style.gridColumn = n.col; d.style.gridRow = n.row;
  d.innerHTML = '<span class="n"></span><b></b><p></p>' + (n.band ? '<div class="band"></div>' : '<span class="tag"></span>');
  d.querySelector('.n').textContent = n.step || ''; d.querySelector('b').textContent = n.title; d.querySelector('p').textContent = n.sub;
  if (n.band) d.querySelector('.band').innerHTML = n.band.map(b => `<span style="background:${{b[1]}};color:${{b[2]}}">${{b[0]}}</span>`).join('');
  else {{ const t = d.querySelector('.tag'); t.textContent = n.tag; if (n.tagc) t.classList.add(n.tagc); }}
  grid.appendChild(d); el[n.id] = d;
  d.addEventListener('mouseenter', () => show(n, d)); d.addEventListener('mouseleave', () => peek.classList.remove('on'));
}});
function show(n, d) {{
  peek.innerHTML = (n.img ? '<img alt="">' : '') + '<b></b><p></p>' + (n.cost ? '<span class="c"></span>' : '');
  if (n.img) peek.querySelector('img').src = n.img;
  peek.querySelector('b').textContent = n.title; peek.querySelector('p').textContent = n.more || n.sub;
  if (n.cost) peek.querySelector('.c').textContent = n.cost;
  const w = wrap.getBoundingClientRect(), r = d.getBoundingClientRect();
  let x = r.left - w.left + r.width / 2 - 160; x = Math.max(10, Math.min(x, w.width - 330));
  let y = r.bottom - w.top + 10; if (y + 260 > w.height) y = Math.max(10, r.top - w.top - (n.img ? 290 : 120));
  peek.style.left = x + 'px'; peek.style.top = y + 'px'; peek.classList.add('on');
}}
function box(id) {{ const w = wrap.getBoundingClientRect(), r = el[id].getBoundingClientRect();
  return {{l: r.left - w.left, r: r.right - w.left, t: r.top - w.top, b: r.bottom - w.top, cx: r.left - w.left + r.width / 2, cy: r.top - w.top + r.height / 2}}; }}
function draw() {{
  [...svg.querySelectorAll('path.e, text, path.l')].forEach(x => x.remove());
  const add = (d, cls, mk) => {{ const p = document.createElementNS('http://www.w3.org/2000/svg', 'path'); p.setAttribute('d', d); p.setAttribute('class', cls);
    p.setAttribute('fill', 'none'); p.setAttribute('stroke', cls === 'l' ? '#B5658A' : '#1E2A47'); p.setAttribute('stroke-width', '1.4');
    if (cls === 'l') p.setAttribute('stroke-dasharray', '5 5'); p.setAttribute('marker-end', 'url(#' + mk + ')'); svg.appendChild(p); return p; }};
  E.forEach(([a, b]) => {{ const A = box(a), B = box(b);
    if (Math.abs(A.cy - B.cy) < 30) add(`M${{A.r}},${{A.cy}} L${{B.l - 2}},${{A.cy}}`, 'e', 'a');
    else if (B.t > A.b) add(`M${{A.cx}},${{A.b}} L${{A.cx}},${{B.t - 2}}`, 'e', 'a');
    else add(`M${{A.cx}},${{A.t}} L${{A.cx}},${{B.b + 2}}`, 'e', 'a'); }});
  L.forEach(([a, b, label]) => {{ const A = box(a), B = box(b); let d, lx, ly, anchor = 'middle';
    if (Math.abs(A.cy - B.cy) < 30) {{ d = `M${{A.l}},${{A.cy}} L${{B.r + 2}},${{B.cy}}`; lx = (A.l + B.r) / 2; ly = A.cy + 16; }}
    else {{ d = `M${{A.l}},${{A.cy}} C${{B.cx}},${{A.cy}} ${{B.cx}},${{A.cy}} ${{B.cx}},${{B.b + 2}}`; lx = B.cx - 8; ly = (A.cy + B.b) / 2; anchor = 'end'; }}
    add(d, 'l', 'ar');
    if (label) {{ const t = document.createElementNS('http://www.w3.org/2000/svg', 'text'); t.setAttribute('class', 'lbl');
      t.setAttribute('x', lx); t.setAttribute('y', ly); t.setAttribute('text-anchor', anchor); t.textContent = label; svg.appendChild(t); }} }});
}}
draw(); window.addEventListener('resize', draw); document.fonts && document.fonts.ready.then(draw);
</script></body></html>"""
