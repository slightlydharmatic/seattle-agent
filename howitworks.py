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
.hw-kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border-top:1px solid var(--ink);margin-top:22px}
.hw-kpis div{padding:14px 16px 0 0}
.hw-kpis b{display:block;font:400 40px/1 var(--serif) !important}
.hw-kpis span{font-size:14px;color:var(--dim);line-height:1.35;display:block;margin-top:6px}
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
.hw-broke{display:grid;gap:0}
.hw-broke div{display:grid;grid-template-columns:minmax(0,1fr) 22px minmax(0,1fr);gap:12px;padding:11px 0;border-bottom:1px solid var(--hair);font-size:14.5px;line-height:1.4}
.hw-broke div span:first-child{color:var(--dim)}
.hw-broke div span:nth-child(2){color:var(--soft);text-align:center}
.hw-next{margin-top:36px;padding:16px 20px;background:var(--tint);border-radius:14px;font-size:15px;line-height:1.5}
.hw-next b{font-weight:500}
@media (max-width:900px){.hw-kpis,.hw-levers,.hw-metrics{grid-template-columns:1fr 1fr}.hw-calls{grid-template-columns:1fr}
  .hw-broke div{grid-template-columns:1fr}.hw-broke div span:nth-child(2){display:none}}
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
  <p>An AI workflow that turns {n_sites} event sites into one weekly list our followers trust, with my team in the loop.</p>
  <div class='hw-kpis'>
    <div><b>5+ hrs</b><span>a week by hand, before</span></div>
    <div><b>2 models</b><span>a cheap one reads, a stronger one judges</span></div>
    <div><b>~{money(est['total'])}</b><span>per weekly run, estimated</span></div>
    <div><b>{e(views)}</b><span>views on our last 5 lists</span></div>
  </div>
</div>
<div class='hw-h'><div class='h2'>The <em>system</em></div><span>Hover a step for what it does, what it costs, and the real screen.</span></div></div>"""


def cost(est: dict) -> str:
    x, c = est["extract"], est["curate"]
    rows = (f"<tr><td>Read pages</td><td><code>{e(x['model'])}</code></td><td class='num'>{x['in'] / 1000:.0f}K in · {x['out'] / 1000:.0f}K out</td>"
            f"<td class='num'>{money(x['usd'])}</td></tr>"
            f"<tr><td>Judge events</td><td><code>{e(c['model'])}</code></td><td class='num'>{c['in'] / 1000:.0f}K in · {c['out'] / 1000:.0f}K out</td>"
            f"<td class='num'>{money(c['usd'])}</td></tr>"
            f"<tr><td>Rules, dedupe, breaker</td><td><code>no model</code></td><td class='num'>0</td><td class='num'>$0</td></tr>"
            f"<tr class='tot'><td>Per weekly run</td><td></td><td class='num'>{est['pages']} pages · {est['events']} events · {est['calls']} judge calls</td>"
            f"<td class='num'>~{money(est['total'])}</td></tr>")
    return f"""
<div class='hw'><div class='hw-h'><div class='h2'>What it <em>costs</em></div><span>~{money(est['month'])} a month in model calls, plus search credits</span></div>
<table class='hw-table'><thead><tr><th>Step</th><th>Model</th><th class='num'>Tokens per run</th><th class='num'>Est.</th></tr></thead>
<tbody>{rows}</tbody></table>
<div class='hw-foot'>Estimate from list prices and written-out token assumptions (costs.py). Next: log real usage from every API response.</div>
<div class='hw-levers'>
  <div><b>Right model per job</b>Volume goes to the cheap model. Only judgment gets the stronger one.</div>
  <div><b>Rules before models</b>Paid or ticketed events never reach a paid call.</div>
  <div><b>Batch and cache</b>20 events per call. Each event is judged once per prompt version.</div>
  <div><b>Readers cost $0</b>The public page reads a saved snapshot, never the APIs.</div>
</div></div>"""


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
    votes = metrics.get("votes", 0)
    ex = "".join(f"<tr><td>{e(t)}</td><td>passes</td><td class='{'ok' if ok else 'no'}'>{e(v)}</td></tr>" for t, v, ok in examples)
    return f"""
<div class='hw'><div class='hw-h'><div class='h2'>The calls <em>I made</em></div></div>
<div class='hw-calls'>{c}</div>
<div class='hw-h'><div class='h2'>Keywords vs. <em>meaning</em></div><span>Why a model is worth paying for here</span></div>
<table class='hw-table'><thead><tr><th>Event (test set)</th><th>Keyword rules</th><th>AI judge</th></tr></thead><tbody>{ex}</tbody></table>
<div class='hw-h'><div class='h2'>How I <em>measure</em> it</div><span>graded against my team's votes</span></div>
<div class='hw-metrics'>
  <div><b>{pct(metrics.get('precision'))}</b><span>Precision: picks we agree with</span></div>
  <div><b>{pct(metrics.get('recall'))}</b><span>Recall: good events it found</span></div>
  <div><b>{pct(metrics.get('close_share'))}</b><span>Sent to a person</span></div>
  <div><b>{votes}</b><span>{'Votes so far' if votes >= 10 else 'Votes so far · grading starts at 10'}</span></div>
</div></div>"""


def broke() -> str:
    items = [
        ("Keywords let a \"free AI webinar\" sales call through", "Added an AI judge for intent"),
        ("A source quietly returned zero events", "Circuit breaker plus per-source warnings"),
        ("One site served last month's events", "Read month-specific pages instead"),
        ("Long pages got cut off mid-list", "Read in overlapping chunks"),
        ("\"Free\" events had ticket links in the details", "Rules for ticket language and prices in text"),
        ("Team votes vanished when the app restarted", "Moved them to a database (Supabase)"),
    ]
    rows = "".join(f"<div><span>{e(a)}</span><span>→</span><span>{e(b)}</span></div>" for a, b in items)
    return f"""
<div class='hw'><div class='hw-h'><div class='h2'>What <em>broke</em></div><span>and what changed</span></div>
<div class='hw-broke'>{rows}</div>
<div class='hw-next'><b>Next:</b> a hand-labeled golden set every prompt change must pass, real token logging, and click tracking to see which picks people actually go to.</div></div>"""
