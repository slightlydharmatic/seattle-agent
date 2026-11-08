"""Copy and layout for the How it works page: short, scannable, built around decisions.

Uses case_study.CSS for the shared look (blue editorial palette, Bodoni + Hanken).
"""
import html

CSS = """
<style>
.hw{--ink:#1E2A47;--dim:#4A577D;--soft:#7A84A3;--hair:rgba(30,42,71,.18);--tint:#EDF2FA;--peri:#5469C4;--rose:#B5658A;
  --serif:'Bodoni Moda',Didot,Georgia,serif;--sans:'Hanken Grotesk','Figtree',sans-serif;--mono:ui-monospace,'SF Mono',Menlo,monospace;
  font-family:var(--sans);color:var(--ink)}
.hw *{font-family:inherit}
.hw [data-testid="stHeaderActionElements"], .hw h1 a, .hw h2 a{display:none !important}
.hw .h1,.hw .h2{font-family:var(--serif) !important;font-weight:400;color:var(--ink);padding:0 !important;letter-spacing:-.01em}
.hw-top{padding:46px 0 8px;display:grid;gap:10px}
.hw-top .h1{font-size:clamp(44px,6vw,72px) !important;line-height:1 !important;margin:0}
.hw-top .h1 em{font-style:italic}
.hw-top p{font-size:19px;color:var(--dim);max-width:52ch;line-height:1.45;margin:0}
.hw-line{display:flex;flex-wrap:wrap;align-items:baseline;gap:6px 14px;margin-top:20px;padding-top:16px;
  border-top:1px solid var(--ink);font-size:16px;color:var(--dim)}
.hw-line b{font:400 30px/1 var(--serif) !important;color:var(--ink);margin-right:4px}
.hw-line .hw-arr,.hw-line .hw-dot{color:var(--soft);font-size:20px}
.hw-cost{position:relative;cursor:pointer;outline:none}
.hw-cost > b{border-bottom:1px dashed var(--soft)}
.hw-cost:hover b,.hw-cost:focus-within b{color:var(--peri)}
.hw-pop{position:absolute;z-index:20;left:-12px;top:calc(100% + 10px);width:440px;max-width:86vw;background:#fff;border:1px solid var(--hair);
  border-radius:14px;box-shadow:0 24px 60px rgba(20,30,70,.18);padding:16px 18px;opacity:0;visibility:hidden;transform:translateY(6px);
  transition:opacity .2s,transform .25s,visibility .2s;cursor:default}
.hw-cost:hover .hw-pop,.hw-cost:focus-within .hw-pop{opacity:1;visibility:visible;transform:none}
.hw-pop b.hw-pop-t{display:block;font:400 22px/1.1 var(--serif) !important;color:var(--ink)}
.hw .hw-pop span.hw-pop-s{display:block;font-size:13px;color:var(--soft);margin:4px 0 8px}
.hw-pop .hw-table{font-size:13.5px}
.hw-pop ul{margin:10px 0 0;padding-left:16px;font-size:13px;line-height:1.45;color:var(--dim)}
.hw-line .hw-pop li b{display:inline;font:500 13px/1.45 var(--sans) !important;color:var(--ink)}
.hw-line .hw-pop b.hw-pop-t{font:400 22px/1.1 var(--serif) !important;margin:0}
.hw .hw-pop span.hw-pop-f{display:block;font-size:12px;color:var(--soft);margin-top:8px}
.hw-h{display:flex;align-items:baseline;gap:14px;margin:52px 0 14px;flex-wrap:wrap}
.hw-h .h2{font-size:34px !important;line-height:1.05 !important;margin:0}
.hw-h .h2 em{font-style:italic}
.hw-h span{font-size:15px;color:var(--soft)}
.hw-table{width:100%;border-collapse:collapse;font-size:14.5px;border:none !important}
.hw-table th,.hw-table td{border-left:none !important;border-right:none !important;border-top:none !important;background:transparent;
  padding:10px 14px 10px 0;text-align:left;vertical-align:top}
.hw-table th{font-weight:500;font-size:12.5px;color:var(--soft);border-bottom:1px solid var(--ink) !important}
.hw-table td{border-bottom:1px solid var(--hair) !important;color:var(--dim)}
.hw-table td:first-child{color:var(--ink);font-weight:500}
.hw-table code{font-family:var(--mono) !important;font-size:12px;background:var(--tint);color:var(--ink) !important;padding:2px 6px;border-radius:5px}
.hw-table tr.tot td{border-bottom:1px solid var(--ink) !important;color:var(--ink);font-weight:500}
.hw-table .num{text-align:right;font-variant-numeric:tabular-nums}
.hw-foot{font-size:13px;color:var(--soft);margin-top:10px;line-height:1.5}
.hw-levers{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-top:16px}
.hw-levers div{background:var(--tint);border-radius:12px;padding:12px 14px;font-size:13.5px;line-height:1.4;color:var(--dim)}
.hw-levers b{display:block;color:var(--ink);font-weight:500;font-size:14.5px;margin-bottom:3px}
.hw-calls{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0 32px}
.hw-calls div{display:grid;grid-template-columns:34px minmax(0,1fr);padding:12px 0;border-bottom:1px solid var(--hair)}
.hw-calls i{font:italic 400 19px var(--serif);color:var(--soft)}
.hw-calls b{font-weight:500;font-size:15.5px}
.hw-calls p{font-size:14px;color:var(--dim);margin:2px 0 0;line-height:1.4}
.hw-metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}
.hw-metrics div{border:1px solid var(--hair);border-radius:12px;padding:12px 14px;background:#fff}
.hw-metrics b{display:block;font:400 30px/1 var(--serif) !important}
.hw-metrics span{font-size:13px;color:var(--dim);display:block;margin-top:6px}
.ok{color:#2F6B53 !important;font-weight:500}.no{color:#A8423A !important;font-weight:500}
.kv{display:grid;grid-template-columns:minmax(0,1fr) 120px minmax(0,1fr);gap:10px;align-items:stretch}
.kv-col{background:#fff;border:1px solid var(--hair);border-radius:16px;padding:16px 18px;display:flex;flex-direction:column;gap:8px}
.kv-k{font:italic 400 22px var(--serif);color:var(--ink)}
.hw .kv p.kv-sub{font-size:14px;color:var(--dim);margin:0 0 4px;line-height:1.45}
.kv-card{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:10px 12px;border-radius:10px;background:var(--tint)}
.kv-card b{font-weight:500;font-size:14.5px;color:var(--ink)}
.kv-tag{font-size:12.5px;white-space:nowrap;padding:3px 9px;border-radius:999px}
.kv-tag.pass{color:var(--soft);background:#fff}
.kv-tag.keep{color:#2F6B53;background:#E6F2EC}.kv-tag.cut{color:#A8423A;background:#F8E4E1}
.kv-mid{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;text-align:center;font-size:13px;color:var(--soft)}
.kv-mid i{font-style:normal;font-size:28px;color:var(--ink)}
.kv-bucket{display:flex;flex-direction:column;gap:6px}
.kv-bucket + .kv-bucket{margin-top:6px}
.kv-bk{font-size:12px;letter-spacing:.08em;text-transform:uppercase;font-weight:600}
.kv-bucket.keep .kv-bk{color:#2F6B53}.kv-bucket.cut .kv-bk{color:#A8423A}
.kv-bucket.keep .kv-card{background:#F4FAF6}.kv-bucket.cut .kv-card{background:#FCF4F3}
.gr{background:#fff;border:1px solid var(--hair);border-radius:16px;padding:18px 20px}
.hw .gr-wait p{font-size:15.5px;color:var(--ink);margin:0 0 12px;line-height:1.5;max-width:70ch}
.gr-bar{height:8px;border-radius:999px;background:var(--tint);overflow:hidden;max-width:420px}
.gr-bar i{display:block;height:100%;background:var(--peri)}
.gr-wait span{display:block;font-size:13px;color:var(--soft);margin-top:6px}
.gr-nums{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}
.gr-nums b{display:block;font:400 40px/1 var(--serif) !important;color:var(--ink)}
.gr-nums span{font-size:14px;color:var(--dim);display:block;margin-top:6px}
@media (max-width:900px){.kv{grid-template-columns:1fr}.kv-mid{flex-direction:row}.kv-mid i{transform:rotate(90deg)}.gr-nums{grid-template-columns:1fr}}
.hw-broke{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
.hw-bk{background:#fff;border:1px solid var(--hair);border-radius:14px;padding:16px 18px;display:flex;flex-direction:column;
  justify-content:space-between;gap:14px;transition:transform .3s cubic-bezier(.2,.8,.2,1),box-shadow .3s}
.hw-bk:hover{transform:translateY(-3px);box-shadow:0 14px 30px rgba(30,50,110,.10)}
.hw .hw-bk p{margin:0}
.hw .hw-bk p.was{font:400 18px/1.3 var(--serif) !important;color:var(--ink)}
.hw .hw-bk p.fix{font-size:14px;color:#2F6B53;display:flex;gap:8px;align-items:baseline;padding-top:12px;border-top:1px solid var(--hair)}
.hw-bk p.fix span{font-weight:600}
.hw-next{margin-top:36px;padding:16px 20px;background:var(--tint);border-radius:14px;font-size:15px;line-height:1.5}
.hw-next b{font-weight:500}
@media (max-width:900px){.hw-levers,.hw-metrics{grid-template-columns:1fr 1fr}.hw-calls{grid-template-columns:1fr}
  .hw-broke{grid-template-columns:1fr}}
</style>
"""


def e(x) -> str:
    return html.escape(str(x))


def money(v) -> str:
    if v is None:
        return "set price"
    return f"${v:.2f}" if v >= 0.1 else f"{v * 100:.1f}¢"


def top(n_sites: int, est: dict, views: str) -> str:
    return f"""
<div class='hw'><div class='hw-top'>
  <div class='h1'>How it <em>works</em></div>
  <p>The AI workflow that turns unstructured data into a list with taste, generating 1M+ views a month.</p>
  <div class='hw-line'>
    <span><b>5+ hrs</b> by hand</span><span class='hw-arr'>→</span>
    <span class='hw-cost' tabindex='0'><b>~{money(est['total'])}</b> by agent{cost_panel(est)}</span>
    <span class='hw-dot'>·</span><span><b>{e(views)}</b> views</span>
  </div>
</div>
<div class='hw-h'><div class='h2'>The <em>system</em></div><span>Hover a step for what it does, what it costs, and the real screen.</span></div></div>"""


def cost_panel(est: dict) -> str:
    """The cost breakdown, shown when someone hovers or taps the cost number."""
    x, c = est["extract"], est["curate"]
    rows = (f"<tr><td>Read pages</td><td><code>{e(x['model'])}</code></td><td class='num'>{money(x['usd'])}</td></tr>"
            f"<tr><td>Judge events</td><td><code>{e(c['model'])}</code></td><td class='num'>{money(c['usd'])}</td></tr>"
            f"<tr><td>Rules, dedupe, breaker</td><td><code>no model</code></td><td class='num'>$0</td></tr>"
            f"<tr class='tot'><td>Per weekly run</td><td>{est['pages']} pages · {est['events']} events</td>"
            f"<td class='num'>~{money(est['total'])}</td></tr>")
    return f"""<div class='hw-pop'>
<b class='hw-pop-t'>What it costs</b><span class='hw-pop-s'>~{money(est['month'])} a month in model calls, plus search credits</span>
<table class='hw-table'><tbody>{rows}</tbody></table>
<ul><li><b>Right model per job.</b> Volume goes to the cheap model; only judgment gets the stronger one.</li>
<li><b>Rules before models.</b> Paid or ticketed events never reach a paid call.</li>
<li><b>Batch and cache.</b> 20 events per call, each judged once per prompt version.</li>
<li><b>Readers cost $0.</b> The public page reads a saved snapshot.</li></ul>
<span class='hw-pop-f'>Estimated from list prices and token assumptions in costs.py.</span></div>"""


def calls(keep_at: int, drop_below: int, metrics: dict, examples: list[tuple]) -> str:
    items = [
        ("Precision over recall", f"{keep_at}+ goes live. A bad pick costs more trust than a missed event."),
        ("People own the gray zone", f"Scores {drop_below} to {keep_at - 1} go to the team, not the model."),
        ("Feedback is the product", "Every thumb overrides instantly, becomes a few-shot example, and is an eval label."),
        ("Explain every decision", "Each event gets an intent, a score, and a one-line reason. Nothing drops silently."),
        ("Policy as code", "No sales funnels, religious services, or partisan events. Cultural festivals stay in."),
        ("Version the prompt", "A new prompt version re-scores everything, so results are comparable."),
        ("Fail safe", "If a run looks broken, it's held. Readers keep last week's list."),
        ("Keep the brand human", "The AI never posts. The graphic and caption are ours."),
    ]
    c = "".join(f"<div><i>{i + 1:02d}</i><span><b>{e(t)}</b><p>{e(d)}</p></span></div>" for i, (t, d) in enumerate(items))

    def pct(v):
        return f"{v:.0%}" if isinstance(v, (int, float)) else "—"

    def card(t, label, score, ok, show_ai):
        tag = (f"<span class='kv-tag {'keep' if ok else 'cut'}'>{e(label)} · {score}</span>" if show_ai
               else "<span class='kv-tag pass'>✓ no banned words</span>")
        return f"<div class='kv-card'><b>{e(t)}</b>{tag}</div>"
    left = "".join(card(t, w, sc, ok, False) for t, w, sc, ok in examples)
    keep = "".join(card(t, w, sc, ok, True) for t, w, sc, ok in examples if ok)
    cut = "".join(card(t, w, sc, ok, True) for t, w, sc, ok in examples if not ok)

    votes = metrics.get("votes", 0)
    need = 10
    if votes >= need:
        grade = (f"<div class='gr-nums'><div><b>{pct(metrics.get('precision'))}</b><span>of the AI's picks, we'd pick too</span></div>"
                 f"<div><b>{pct(metrics.get('recall'))}</b><span>of the events we'd pick, the AI found</span></div>"
                 f"<div><b>{pct(metrics.get('close_share'))}</b><span>sent to us as close calls</span></div></div>")
    else:
        grade = (f"<div class='gr-wait'><p>Every thumbs up or down from the team is a grade. After {need}, this shows "
                 "how often the AI's picks match ours, and how many good events it finds.</p>"
                 f"<div class='gr-bar'><i style='width:{min(votes, need) / need:.0%}'></i></div>"
                 f"<span>{votes} of {need} votes</span></div>")
    return f"""
<div class='hw'><div class='hw-h'><div class='h2'>Our AI <em>product calls</em></div></div>
<div class='hw-calls'>{c}</div>
<div class='hw-h'><div class='h2'>Why a model, <em>not keywords</em></div><span>Four real test events, sorted two ways</span></div>
<div class='kv'>
  <div class='kv-col'><span class='kv-k'>A keyword filter</span><p class='kv-sub'>All four are free with no banned words, so it lets every one through.</p>{left}</div>
  <div class='kv-mid'><span>reads what each<br>event is for</span><i>→</i></div>
  <div class='kv-col'><span class='kv-k'>Our AI judge</span>
    <div class='kv-bucket keep'><span class='kv-bk'>On the list</span>{keep}</div>
    <div class='kv-bucket cut'><span class='kv-bk'>Left off</span>{cut}</div></div>
</div>
<div class='hw-h'><div class='h2'>How we <em>grade</em> it</div><span>against our own team's votes</span></div>
<div class='gr'>{grade}</div></div>"""


def broke() -> str:
    items = [
        ("Keyword rules let a free AI webinar, really a sales pitch, through", "An AI judge that reads intent"),
        ("A source quietly returned zero events", "Circuit breaker and per-source alerts"),
        ("One site served last month's events", "Read month-specific pages"),
        ("Long pages got cut off mid-list", "Read in overlapping chunks"),
        ("\"Free\" events hid ticket links", "Rules for ticket language and prices"),
        ("Team votes vanished on restart", "Moved to a database (Supabase)"),
    ]
    cards = "".join(f"<div class='hw-bk'><p class='was'>{e(a)}</p><p class='fix'><span>✓</span>{e(b)}</p></div>"
                    for a, b in items)
    return f"""
<div class='hw'><div class='hw-h'><div class='h2'>What <em>broke</em></div><span>and how we fixed it</span></div>
<div class='hw-broke'>{cards}</div>
<div class='hw-next'><b>Next:</b> a hand-labeled golden set every prompt change must pass, real token logging, and click tracking to see which picks people actually go to.</div></div>"""
