"""The case study at the top of the AI curation page.

Framed around decisions: the problem, the architecture and why, the evaluation
layer (the moat), and what broke and what changed. Every claim here is true of
this codebase; numbers that aren't measured yet say so.
"""
import html

from config import DEFAULT_FILTERS

CSS = """
<style>
.cs{--ink:#1E2A47;--dim:#4A577D;--soft:#6B7699;--hair:rgba(30,42,71,.22);--blue:#DCE6F3;--blue2:#EDF2FA;
  --peri:#5469C4;--blush:#F5DDE7;--rose:#A65A7D;--serif:'Bodoni Moda',Didot,Georgia,serif;
  --sans:'Hanken Grotesk','Figtree',-apple-system,sans-serif;font-family:var(--sans);color:var(--ink)}
.cs *{font-family:inherit}
.cs .serif, .cs h1, .cs h2, .cs h3{font-family:var(--serif) !important;font-weight:400;letter-spacing:-.01em;color:var(--ink)}
.cs-hero{background:var(--blue);border-radius:20px;padding:34px 36px 30px;margin-bottom:8px;position:relative;overflow:hidden}
.cs-hero:after{content:"";position:absolute;width:420px;height:300px;right:-80px;top:-90px;border-radius:50%;
  background:var(--blush);filter:blur(70px);opacity:.9}
.cs-hero > *{position:relative;z-index:1}
.cs-eyebrow{font-size:14px;color:var(--soft);letter-spacing:.04em;margin-bottom:14px}
.cs-hero h1{font-size:clamp(40px,5.2vw,64px) !important;line-height:1.02 !important;margin:0 0 16px;padding:0 !important;max-width:18ch}
.cs-hero h1 em{font-style:italic}
.cs-hero p.lead{font-size:19px;line-height:1.5;color:var(--dim);max-width:60ch;margin:0}
.cs-facts{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));margin-top:28px;border-top:1px solid var(--hair)}
.cs-facts div{padding:14px 18px 0 0}
.cs-facts span{display:block;font-size:13px;color:var(--soft)}
.cs-facts b{display:block;font-weight:500;font-size:15px;margin-top:3px;line-height:1.4}

.cs-sec{display:grid;grid-template-columns:120px minmax(0,1fr);gap:24px;padding:40px 0 8px;border-top:1px solid var(--hair);margin-top:40px}
.cs-num{font:italic 400 64px/0.9 var(--serif) !important;color:var(--ink)}
.cs-sec h2{font-size:38px !important;line-height:1.08 !important;margin:0 0 6px;padding:0 !important}
.cs-sec h2 em{font-style:italic}
.cs-sec .kicker{font-size:17px;color:var(--dim);max-width:62ch;line-height:1.55;margin:0 0 22px}
.cs h3{font-size:24px !important;margin:26px 0 12px;padding:0 !important}

.cs-before{display:grid;grid-template-columns:minmax(0,.9fr) minmax(0,1.1fr);gap:22px;align-items:stretch}
.cs-big{background:var(--blue2);border-radius:16px;padding:22px 24px}
.cs-big b{display:block;font:400 72px/1 var(--serif) !important}
.cs-big span{font-size:15px;color:var(--dim)}
.cs-steps{display:grid;gap:0}
.cs-steps div{display:grid;grid-template-columns:28px minmax(0,1fr);gap:10px;padding:12px 0;border-bottom:1px solid var(--hair);font-size:16px;line-height:1.45}
.cs-steps div:last-child{border-bottom:none}
.cs-steps i{font:italic 400 18px var(--serif);color:var(--soft)}
.cs-steps small{display:block;color:var(--soft);font-size:14px}

.cs-three{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}
.cs-card{border:1px solid var(--hair);border-radius:16px;padding:18px 20px;background:#fff;transition:transform .35s cubic-bezier(.2,.8,.2,1),box-shadow .35s}
.cs-card:hover{transform:translateY(-4px);box-shadow:0 18px 40px rgba(30,50,110,.10)}
.cs-card .t{font:italic 400 22px/1.15 var(--serif) !important;margin-bottom:8px;display:block}
.cs-card p{font-size:15px;color:var(--dim);line-height:1.5;margin:0}
.cs-card .no{display:inline-block;margin-top:12px;font-size:13px;color:var(--rose);background:var(--blush);padding:3px 10px;border-radius:999px}
.cs-gap{margin-top:16px;padding:16px 20px;border-left:2px solid var(--peri);background:var(--blue2);border-radius:0 12px 12px 0;font-size:17px;line-height:1.5}
.cs-gap b{font-weight:500}

.cs-map{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:0;padding:4px 0 6px}
.cs-node{min-width:0;padding:14px 12px 12px;border-top:2px solid var(--ink);position:relative;transition:background .3s}
.cs-node:hover{background:var(--blue2)}
.cs-node small{display:block;font-size:12px;color:var(--soft);letter-spacing:.04em}
.cs-node b{display:block;font:400 18px/1.15 var(--serif) !important;margin:6px 0 6px}
.cs-node p{font-size:13px;overflow-wrap:anywhere;color:var(--dim);line-height:1.4;margin:0}
.cs-node.guard{border-top-color:var(--peri)}
.cs-node.human{border-top-color:var(--rose)}
.cs-node + .cs-node:before{content:"→";position:absolute;left:-7px;top:-13px;font-size:14px;color:var(--soft);background:#FBF9F7;padding:0 2px}
@media (max-width:900px){.cs-map{row-gap:14px}}
.cs-legend{display:flex;gap:18px;font-size:13px;color:var(--soft);margin-top:10px;flex-wrap:wrap}
.cs-legend i{display:inline-block;width:18px;height:2px;vertical-align:middle;margin-right:6px}
.cs-loop{font-size:14px;color:var(--rose);margin-top:6px}

.cs-table{width:100%;border-collapse:collapse;font-size:15px;border:none !important}
.cs-table th,.cs-table td{border-left:none !important;border-right:none !important;border-top:none !important;background:transparent}
.cs-table th{text-align:left;font-weight:500;font-size:13px;color:var(--soft);padding:8px 12px 8px 0;border-bottom:1px solid var(--ink)}
.cs-table td{padding:12px 12px 12px 0;border-bottom:1px solid var(--hair);vertical-align:top;line-height:1.45;color:var(--dim)}
.cs-table td:first-child{color:var(--ink);font-weight:500;white-space:nowrap}
.cs-table tr{transition:background .25s}.cs-table tbody tr:hover{background:var(--blue2)}

.cs-vs{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:14px}
.cs-pane{border-radius:16px;padding:18px 20px;font-size:14px;line-height:1.55}
.cs-pane.old{background:#F3F1EE;color:#6E6676}
.cs-pane.new{background:var(--blue2);color:var(--ink)}
.cs-pane .lbl{display:block;font:italic 400 20px var(--serif) !important;margin-bottom:10px;color:var(--ink)}
.cs-pane code{font-family:ui-monospace,Menlo,monospace !important;font-size:12.5px;color:#1E2A47 !important;background:rgba(255,255,255,.7);padding:1px 5px;border-radius:4px}
.cs-pane blockquote{margin:0;padding:0 0 0 12px;border-left:2px solid var(--peri);font-size:14.5px}
.v-ok{color:#3F7A63;font-weight:500}.v-no{color:#B14A40;font-weight:500}

.cs-versions{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border-top:1px solid var(--ink)}
.cs-versions div{padding:14px 16px 0 0}
.cs-versions b{font:italic 400 22px var(--serif) !important;display:block}
.cs-versions p{font-size:14px;color:var(--dim);line-height:1.45;margin:6px 0 0}

.cs-guards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0 28px}
.cs-guards div{padding:14px 0;border-bottom:1px solid var(--hair)}
.cs-guards b{font-weight:500;font-size:16px;display:block}
.cs-guards p{font-size:14.5px;color:var(--dim);margin:4px 0 0;line-height:1.5}
.cs-guards .rule{font-size:13px;color:var(--peri);margin-top:6px;display:block}

.cs-metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}
.cs-metric{background:var(--blue2);border-radius:14px;padding:16px 18px}
.cs-metric b{display:block;font:400 34px/1.05 var(--serif) !important}
.cs-metric span{font-size:14px;color:var(--dim);display:block;margin-top:4px}
.cs-metric small{font-size:12.5px;color:var(--soft);display:block;margin-top:6px}

.cs-fail{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.cs-fail .cs-card .t{font-size:20px !important}
.cs-fail .fix{font-size:15px;color:var(--ink);margin-top:10px;padding-top:10px;border-top:1px solid var(--hair);line-height:1.5}
.cs-fail .fix:before{content:"Fix  ";color:var(--peri);font-weight:500}
.cs-pivot{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:0;border:1px solid var(--hair);border-radius:16px;overflow:hidden}
.cs-pivot div{padding:18px 22px}
.cs-pivot div + div{border-left:1px solid var(--hair);background:var(--blush)}
.cs-pivot .lbl{font:italic 400 22px var(--serif) !important;display:block;margin-bottom:8px}
.cs-pivot ul{margin:0;padding-left:18px;font-size:15px;line-height:1.6;color:var(--dim)}
.cs-quote{font:italic 400 26px/1.3 var(--serif) !important;max-width:34ch;margin:30px 0 0 !important;color:var(--ink)}
.cs-end{margin-top:46px;padding-top:18px;border-top:1px solid var(--ink);font-size:14px;color:var(--soft)}
@media (max-width:900px){.cs-sec{grid-template-columns:1fr}.cs-map{grid-template-columns:repeat(2,minmax(0,1fr))}.cs-before,.cs-three,.cs-vs,.cs-guards,.cs-fail,.cs-pivot,
  .cs-facts,.cs-versions,.cs-metrics{grid-template-columns:1fr}.cs-pivot div + div{border-left:none}}
@media (prefers-reduced-motion:reduce){.cs *{transition:none !important}}
</style>
"""


def e(x) -> str:
    return html.escape(str(x))


def hero(n_sites: int) -> str:
    return f"""
<div class='cs'><div class='cs-hero'>
  <div class='cs-eyebrow'>case study · seattle unlocked</div>
  <h1>Teaching an AI what <em>worth going to</em> means</h1>
  <p class='lead'>Curating free Seattle events for 80k followers took me 5+ hours a week, and no tool could tell a
  community meetup from a sales pitch dressed up as one. I built an agent that does the reading, judges intent
  instead of keywords, and hands my team only the close calls.</p>
  <div class='cs-facts'>
    <div><span>My role</span><b>Product, design, and build</b></div>
    <div><span>Users</span><b>Seattle locals 28 to 52, and our curation team</b></div>
    <div><span>System</span><b>{n_sites} sources · 2 models · 1 human review band</b></div>
    <div><span>Status</span><b>Live, collecting eval labels</b></div>
  </div>
</div></div>"""


def problem() -> str:
    return """
<div class='cs'><div class='cs-sec'><div class='cs-num'>01</div><div>
  <h2>The problem, and the <em>before</em></h2>
  <p class='kicker'>Finding events was never the hard part. Judging them was. Every week the same three jobs, all by hand.</p>
  <div class='cs-before'>
    <div class='cs-big'><b>5+</b><span>hours a week, every week, before anything was posted</span></div>
    <div class='cs-steps'>
      <div><i>1</i><span>Search six listing sites, Instagram, and Google<small>Different formats, repeats across sites, pages that silently go stale</small></span></div>
      <div><i>2</i><span>Check each one is really free<small>"Free" on the listing, a ticket link or cover charge in the details</small></span></div>
      <div><i>3</i><span>Decide if it's worth our readers' Saturday<small>The slow part: is this a real community event, or a funnel?</small></span></div>
    </div>
  </div>
  <h3>Why the tools I tried didn't work</h3>
  <div class='cs-three'>
    <div class='cs-card'><span class='t'>Eventbrite and site filters</span>
      <p>"Free" is a price field, not a judgment. Webinars that end in a sales call and free-to-RSVP, pay-at-the-door events all pass.</p>
      <span class='no'>filters price, not intent</span></div>
    <div class='cs-card'><span class='t'>Scrolling Instagram and Google</span>
      <p>Great for discovery, impossible to make complete or repeatable. No record of what I saw, skipped, or why.</p>
      <span class='no'>no coverage, no audit trail</span></div>
    <div class='cs-card'><span class='t'>ChatGPT by hand</span>
      <p>Could judge one pasted list, but forgot our taste every week, gave different answers to the same event, and couldn't be checked later.</p>
      <span class='no'>no memory, no consistency</span></div>
  </div>
  <div class='cs-gap'><b>The real gap:</b> judgment at volume that remembers our taste, explains itself, and knows when to ask a person.</div>
</div></div></div>"""


def architecture(extract_model: str, curator_model: str) -> str:
    curator = curator_model if curator_model != extract_model else f"{curator_model} (upgrade ready)"
    nodes = [
        ("", "Inputs", f"6 listing sites + this month's and next two months' pages"),
        ("", "Extract", f"{extract_model} reads pages in chunks into structured events"),
        ("guard", "Clean + rules", "Merge repeats, check date and venue, drop paid, ticketed, real estate"),
        ("", "Curate", f"{curator} judges intent, scores 0 to 100, says why"),
        ("guard", "Guardrails", "Review band, circuit breaker, every drop logged"),
        ("human", "Team", "Thumbs override the model and become its examples"),
        ("human", "Output", "Picks, our template, Instagram"),
    ]
    flow = "".join(f"<div class='cs-node {c}'><small>{i + 1:02d}</small><b>{e(t)}</b><p>{e(d)}</p></div>"
                   for i, (c, t, d) in enumerate(nodes))
    stack = [
        ("LangGraph", "Each step is a node, so cheap steps rerun on their own without re-paying for search and extraction.",
         "More setup than a single script."),
        ("Tavily", "Search and clean page text in one API call, from a list of sites I trust.", "Paid per call; some sites block readers."),
        (extract_model, "Extraction is high volume and structured. A small model does it well for cents.",
         "Misses nuance, which is why judging is a separate step."),
        ("Separate curator model", "Judgment is where quality lives, so it gets its own prompt, version, and model setting.",
         "Costs more per event, so scores are cached and each event is judged once."),
        ("Streamlit", "One Python codebase from pipeline to team UI. Shipped in days.",
         "Less design control; I built custom HTML on top."),
        ("Supabase", "Votes, rules, and allowed events survive restarts. Locked down with row level security.",
         "One more service and key to manage."),
        ("GitHub Actions", "Free weekly schedule that commits a snapshot, so readers never trigger API calls.",
         "Runs on a timer, not on demand."),
        ("Claude", "Pair-built with Claude for fast prototyping, tests, and refactors.", "I still review every change."),
    ]
    rows = "".join(f"<tr><td>{e(a)}</td><td>{e(b)}</td><td>{e(c)}</td></tr>" for a, b, c in stack)
    return f"""
<div class='cs'><div class='cs-sec'><div class='cs-num'>02</div><div>
  <h2>The architecture, and <em>why</em></h2>
  <p class='kicker'>Two models with two different jobs. A cheap one reads, a stronger one judges, and deterministic
  rules sit in front so the model never pays to look at something a keyword can rule out.</p>
  <div class='cs-map'>{flow}</div>
  <div class='cs-legend'><span><i style='background:#1E2A47'></i>machine</span><span><i style='background:#5469C4'></i>guardrail</span>
    <span><i style='background:#A65A7D'></i>person</span></div>
  <div class='cs-loop'>↺ Team votes flow back into step 04 as few-shot examples on the next run.</div>
  <h3>Stack trade-offs</h3>
  <table class='cs-table'><thead><tr><th>Choice</th><th>Why</th><th>Trade-off</th></tr></thead><tbody>{rows}</tbody></table>
  <h3>Walk through it</h3>
</div></div></div>"""


def moat(prompt_version: str, keep_at: int, drop_below: int, metrics: dict) -> str:
    kw = DEFAULT_FILTERS["ticket_terms"][:5] + DEFAULT_FILTERS["topics"]["Real estate"][:3]
    kw_html = ", ".join(f"<code>{e(k)}</code>" for k in kw)
    examples = [
        ("Free AI Webinar: Grow Your Business 10x", "pass", "Marketing pitch · 14", False),
        ("Seattle AI Builders Meetup", "pass", "High-value networking · 86", True),
        ("Sunday Revival Worship Night", "pass", "Religious service · 8", False),
        ("Diwali Festival of Lights", "pass", "Community gathering · 92", True),
    ]
    ex = "".join(f"<tr><td>{e(t)}</td><td>{k}</td><td class='{'v-ok' if ok else 'v-no'}'>{e(a)} · "
                 f"{'keep' if ok else 'filtered'}</td></tr>" for t, k, a, ok in examples)
    m = metrics
    def val(v, fmt="{:.0%}"):
        return fmt.format(v) if isinstance(v, (int, float)) else "—"
    return f"""
<div class='cs'><div class='cs-sec'><div class='cs-num'>03</div><div>
  <h2>The moat: <em>taste</em>, and how it's checked</h2>
  <p class='kicker'>Anyone can call a model. The product is the layer that decides what good looks like, catches
  the model when it's wrong, and gets better from my team's judgment.</p>

  <h3>From keywords to meaning</h3>
  <div class='cs-vs'>
    <div class='cs-pane old'><span class='lbl'>v0 · keyword rules</span>
      Matched words like {kw_html}. Fast and predictable, but every event below sails through: none of them
      mention a price or a banned word.</div>
    <div class='cs-pane new'><span class='lbl'>{e(prompt_version)} · judged by meaning</span>
      <blockquote>"Judge each event on its intent and value to a curious local, not on keywords. A community AI meetup
      with named hosts and talks is high-value networking; a free AI webinar that ends in a product demo is a
      marketing pitch."</blockquote></div>
  </div>
  <table class='cs-table' style='margin-top:14px'><thead><tr><th>Event (test set)</th><th>Keywords</th><th>Curator</th></tr></thead>
    <tbody>{ex}</tbody></table>

  <h3>How the instructions evolved</h3>
  <div class='cs-versions'>
    <div><b>v0</b><p>Keyword rules only. Caught prices and tickets, missed every disguised pitch.</p></div>
    <div><b>v1</b><p>LLM judges intent and returns a score and a one-line reason, so every decision explains itself.</p></div>
    <div><b>v2</b><p>Added our mission and a policy: no sales funnels, religious services, or partisan events. Diwali and MLK Day stay in.</p></div>
    <div><b>v3</b><p>Added the reader: Seattle locals 28 to 52, outgoing, community-minded, low-cost, adventurous. "Would this person be glad they went?"</p></div>
  </div>

  <h3>Guardrails</h3>
  <div class='cs-guards'>
    <div><b>Rules before the model</b><p>Price, ticket, and topic rules run first. Cheap, predictable, and they keep obvious misses out of the prompt.</p></div>
    <div><b>Validation</b><p>An event with no date, no venue, or outside the window is held with a written reason, never guessed at.</p></div>
    <div><b>A review band, not a cutoff</b><p>The model isn't trusted on close calls. Tuned for precision, because one spammy pick costs reader trust.</p>
      <span class='rule'>≥ {keep_at} list · {drop_below} to {keep_at - 1} a person decides · &lt; {drop_below} filtered</span></div>
    <div><b>People outrank the model</b><p>A thumb overrides the score immediately, and the latest votes become few-shot examples on the next run.</p>
      <span class='rule'>8 recent downvotes + 4 upvotes go into the prompt</span></div>
    <div><b>Circuit breaker</b><p>A run that looks broken never replaces the public list. It's held for the team to publish or discard.</p>
      <span class='rule'>trips if events halve, &gt; 50% of pages fail, sources go silent, or the AI drops &gt; 60%</span></div>
    <div><b>Versioned, cached, logged</b><p>Scores are tied to the prompt version, so a new version re-scores everything. Every filtered event keeps its reason.</p>
      <span class='rule'>nothing is dropped silently</span></div>
  </div>

  <h3>Trust metrics</h3>
  <div class='cs-metrics'>
    <div class='cs-metric'><b>{val(m.get('precision'))}</b><span>Precision at the keep line</span><small>Of picks, how many the team agrees with</small></div>
    <div class='cs-metric'><b>{val(m.get('recall'))}</b><span>Recall at the keep line</span><small>Of events the team wants, how many the AI found</small></div>
    <div class='cs-metric'><b>{val(m.get('close_share'))}</b><span>Sent to a person</span><small>Share of scored events in the review band</small></div>
    <div class='cs-metric'><b>{m.get('votes', 0)}</b><span>Team labels</span><small>{'Enough to measure' if m.get('votes', 0) >= 10 else 'Measuring starts at 10'}</small></div>
  </div>
</div></div></div>"""


def failures(keep_at: int = 70, drop_below: int = 40) -> str:
    cards = [
        ("Keywords couldn't read intent", "A \"Free AI Webinar: Grow Your Business 10x\" passed every rule. So did a revival night and a campaign event.",
         "Added the semantic curator, with keywords kept as a cheap first pass."),
        ("A source went quiet, and nothing errored", "Greater Seattle on the Cheap started returning zero events. The list just got thinner.",
         "Circuit breaker plus a per-source warning when a usual source returns nothing."),
        ("The data was a month old", "One site's main page served last month's events from cache. Valid-looking, completely stale.",
         "Read that site's month-specific pages for this month and the next two."),
        ("Long pages got cut off", "Big listing pages blew past what one extraction call could read, so later events vanished.",
         "Read pages in overlapping chunks, so an event split across a break still shows up whole."),
        ("\"Free\" wasn't free", "Ticket links, cover charges, and prices buried in descriptions slipped past the cost field.",
         "Separate rules for ticket language and dollar amounts in the text, each with its own reason."),
        ("The team's work vanished", "The hosted app wipes its disk on restart, taking votes and filter edits with it.",
         "Moved votes, rules, and allowed events to Supabase."),
    ]
    c = "".join(f"<div class='cs-card'><span class='t'>{e(t)}</span><p>{e(p)}</p><div class='fix'>{e(f)}</div></div>"
                for t, p, f in cards)
    return f"""
<div class='cs'><div class='cs-sec'><div class='cs-num'>04</div><div>
  <h2>What failed, and <em>what changed</em></h2>
  <p class='kicker'>None of the hard failures were dramatic. They were quiet: a thinner list, a stale page, a pitch
  that looked like a meetup. The fixes are mostly about making the quiet failures loud.</p>
  <div class='cs-fail'>{c}</div>
  <h3>The pivot: where I pulled automation back</h3>
  <div class='cs-pivot'>
    <div><span class='lbl'>Automated</span><ul><li>Reading every site, every week</li><li>Cleaning, merging, and fact checks</li>
      <li>First-pass judgment with a written reason</li><li>Holding broken runs</li></ul></div>
    <div><span class='lbl'>Kept human, on purpose</span><ul><li>Every close call (scores {drop_below} to {keep_at - 1})</li><li>Publishing a held run</li>
      <li>The graphic and the caption, because that's our voice</li><li>Client CRM: built, then paused until the core loop is proven</li></ul></div>
  </div>
  <p class='cs-quote'>The AI never posts. It narrows a week of listings down to the decisions only we can make.</p>
  <div class='cs-end'>Next: a hand-labeled golden set that every prompt change must pass, click tracking on picks, and one-click export into our template.</div>
</div></div></div>"""
