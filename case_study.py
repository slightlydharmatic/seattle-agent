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
.cs [data-testid="stHeaderActionElements"], .cs h1 a, .cs h2 a{display:none !important}
.cs .serif, .cs h1, .cs h2, .cs h3{font-family:var(--serif) !important;font-weight:400;letter-spacing:-.01em;color:var(--ink)}
.cs-goto{text-align:center;padding:72px 16px 64px;display:grid;justify-items:center;gap:16px}
.cs-goto h1{font-size:clamp(40px,5.4vw,68px) !important;line-height:1.02 !important;max-width:15ch;margin:0;padding:0 !important;text-wrap:balance}
.cs-goto h1 em{font-style:italic}
.cs-goto p{font-size:19px;color:var(--dim);max-width:46ch;line-height:1.5;margin:0}
.cs-btn{display:inline-block;margin-top:8px;background:var(--ink);color:#fff !important;text-decoration:none !important;border-radius:999px;
  padding:13px 24px;font-size:16px;transition:transform .3s cubic-bezier(.2,.8,.2,1),box-shadow .3s}
.cs-btn:hover{transform:translateY(-2px);box-shadow:0 12px 28px rgba(30,42,71,.25)}
.cs-hiw{padding:24px 0 22px;border-top:1px solid var(--hair);display:grid;gap:8px}
.cs-hiw h2{font-size:clamp(32px,4vw,46px) !important;line-height:1.05 !important;margin:0;padding:0 !important;max-width:22ch}
.cs-hiw h2 em{font-style:italic}
.cs-hiw p{font-size:17px;color:var(--dim);margin:0}
.cs-hero{background:var(--blue);border-radius:20px;padding:34px 36px 30px;margin:56px 0 8px;position:relative;overflow:hidden}
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
  <div class='cs-eyebrow'>the case study</div>
  <h1>Teaching an AI what <em>worth going to</em> means</h1>
  <p class='lead'>I run Seattle Unlocked, a free events page with about 80k followers. Every week I spent 5+ hours
  finding events, checking they were actually free, and weeding out the ones that were secretly sales pitches.
  So I built an agent to do the first pass. Now my team and I only make the tricky calls.</p>
  <div class='cs-facts'>
    <div><span>What I did</span><b>Product, design, and the build</b></div>
    <div><span>Who it's for</span><b>Seattle locals 28 to 52, and our curation team</b></div>
    <div><span>Under the hood</span><b>{n_sites} sites, 2 models, and people for the close calls</b></div>
    <div><span>Where it's at</span><b>Live, and collecting our votes to grade it</b></div>
  </div>
</div></div>"""


def problem() -> str:
    return """
<div class='cs'><div class='cs-sec'><div class='cs-num'>01</div><div>
  <h2>Where it <em>started</em></h2>
  <p class='kicker'>Finding events was easy. Deciding which ones deserved a spot on our page took forever.
  Here's what my week used to look like.</p>
  <div class='cs-before'>
    <div class='cs-big'><b>5+</b><span>hours a week before we posted a single thing</span></div>
    <div class='cs-steps'>
      <div><i>1</i><span>Dig through six event sites, Instagram, and Google<small>Same event on three sites, in three formats</small></span></div>
      <div><i>2</i><span>Make sure "free" really meant free<small>A lot of them had a ticket link or a cover charge hiding in the details</small></span></div>
      <div><i>3</i><span>Ask, would our followers actually want to go?<small>This was the slow part. Lots of "free" events are really there to sell you something.</small></span></div>
    </div>
  </div>
  <h3>What I tried first</h3>
  <div class='cs-three'>
    <div class='cs-card'><span class='t'>Eventbrite's free filter</span>
      <p>It only knows the price. A free webinar that ends in a sales call looks exactly like a neighborhood potluck to it.</p></div>
    <div class='cs-card'><span class='t'>Scrolling Instagram and Google</span>
      <p>Fun for finding things, but I could never tell if I'd missed something, and I had no record of why I passed on an event.</p></div>
    <div class='cs-card'><span class='t'>Pasting lists into ChatGPT</span>
      <p>It helped one list at a time, then forgot everything we liked by the next week. Every Monday started from scratch.</p></div>
  </div>
  <div class='cs-gap'>What I actually needed was something that could judge events the way we do, remember what we like,
  and ask us when it wasn't sure.</div>
</div></div></div>"""


def architecture(extract_model: str, curator_model: str) -> str:
    curator = curator_model if curator_model != extract_model else f"{curator_model}, with room to upgrade"
    nodes = [
        ("", "Find", "Six Seattle sites, plus pages for this month and the next two"),
        ("", "Read", f"{extract_model} turns each page into a clean list of events"),
        ("guard", "Clean up", "Drop repeats, anything paid or ticketed, and real estate pitches"),
        ("", "Judge", f"{curator} scores each event and says why"),
        ("guard", "Safety net", "Unsure scores go to us. Broken runs get held."),
        ("human", "Us", "Thumbs up or down. It learns from every one."),
        ("human", "Post", "Our picks, our template, our Instagram"),
    ]
    flow = "".join(f"<div class='cs-node {c}'><small>{i + 1:02d}</small><b>{e(t)}</b><p>{e(d)}</p></div>"
                   for i, (c, t, d) in enumerate(nodes))
    stack = [
        ("LangGraph", "Each step runs on its own, so I can redo the cheap parts without paying to search again.",
         "Takes more setup than one big script."),
        ("Tavily", "Searches and reads web pages in one go, only from sites I trust.", "Costs a little per page, and a few sites block it."),
        (extract_model, "Reading pages is a lot of simple work. A small model does it well for pennies.",
         "It's not great at nuance, so it doesn't make the judgment calls."),
        ("A separate judging model", "Judging is where quality matters, so it gets its own instructions and can use a smarter model.",
         "Costs more per event, so each event only gets judged once."),
        ("Streamlit", "Everything in Python, from the pipeline to the screen my team uses. Up and running in days.",
         "Harder to make pretty. I added my own design on top."),
        ("Supabase", "Our votes and settings stick around when the app restarts, and stay private.",
         "One more account and key to keep safe."),
        ("GitHub Actions", "Runs the whole thing every Monday for free, so visitors never cost us anything.",
         "Weekly, not instant."),
        ("Claude", "My build partner for prototyping, tests, and cleanup.", "I still read every change."),
    ]
    rows = "".join(f"<tr><td>{e(a)}</td><td>{e(b)}</td><td>{e(c)}</td></tr>" for a, b, c in stack)
    return f"""
<div class='cs'><div class='cs-sec'><div class='cs-num'>02</div><div>
  <h2>How it's <em>built</em></h2>
  <p class='kicker'>Two AI models with different jobs. A cheap one does the reading. A smarter one does the judging.
  Simple rules go first so we never pay a model to look at something obviously off.</p>
  <div class='cs-map'>{flow}</div>
  <div class='cs-legend'><span><i style='background:#1E2A47'></i>the agent</span><span><i style='background:#5469C4'></i>safety checks</span>
    <span><i style='background:#A65A7D'></i>us</span></div>
  <div class='cs-loop'>↺ Our thumbs go back into step 4, so next week it judges a little more like us.</div>
  <h3>Why these tools</h3>
  <table class='cs-table'><thead><tr><th>Tool</th><th>Why I picked it</th><th>The catch</th></tr></thead><tbody>{rows}</tbody></table>
</div></div></div>"""


def moat(prompt_version: str, keep_at: int, drop_below: int, metrics: dict) -> str:
    kw = DEFAULT_FILTERS["ticket_terms"][:5] + DEFAULT_FILTERS["topics"]["Real estate"][:3]
    kw_html = ", ".join(f"<code>{e(k)}</code>" for k in kw)
    examples = [
        ("Free AI Webinar: Grow Your Business 10x", "let it in", "Sales pitch, scored 14", False),
        ("Seattle AI Builders Meetup", "let it in", "Real meetup, scored 86", True),
        ("Sunday Revival Worship Night", "let it in", "Religious service, scored 8", False),
        ("Diwali Festival of Lights", "let it in", "Community festival, scored 92", True),
    ]
    ex = "".join(f"<tr><td>{e(t)}</td><td>{k}</td><td class='{'v-ok' if ok else 'v-no'}'>{e(a)}, "
                 f"{'on the list' if ok else 'left off'}</td></tr>" for t, k, a, ok in examples)
    m = metrics

    def val(v, fmt="{:.0%}"):
        return fmt.format(v) if isinstance(v, (int, float)) else "—"
    votes = m.get("votes", 0)
    return f"""
<div class='cs'><div class='cs-sec'><div class='cs-num'>03</div><div>
  <h2>How I keep it <em>honest</em></h2>
  <p class='kicker'>Calling an AI is the easy part. The real work is teaching it our taste, catching it when it's
  wrong, and letting it learn from us.</p>

  <h3>Words vs. meaning</h3>
  <div class='cs-vs'>
    <div class='cs-pane old'><span class='lbl'>Version 0: keyword rules</span>
      I started by blocking words like {kw_html}. That caught prices and tickets. But every event in the table
      below got through, because none of them used a blocked word.</div>
    <div class='cs-pane new'><span class='lbl'>Today ({e(prompt_version)}): it reads for meaning</span>
      <blockquote>"Judge each event on its intent and value to a curious local, not on keywords."</blockquote>
      <p style='margin:10px 0 0'>It's the line I'd give a new teammate: a meetup with real hosts and talks is great;
      a free webinar that ends in a product demo is an ad.</p></div>
  </div>
  <table class='cs-table' style='margin-top:14px'><thead><tr><th>Event (from our test set)</th><th>Keyword rules</th><th>The AI</th></tr></thead>
    <tbody>{ex}</tbody></table>

  <h3>How the instructions grew up</h3>
  <div class='cs-versions'>
    <div><b>v0</b><p>Keyword rules. Caught prices, missed every sneaky pitch.</p></div>
    <div><b>v1</b><p>The AI reads each event, gives it a score, and tells us why in one line.</p></div>
    <div><b>v2</b><p>I wrote down what we stand for: no sales pitches, religious services, or partisan events. Diwali and MLK Day are still in.</p></div>
    <div><b>v3</b><p>I described our people: Seattle locals 28 to 52 who love meeting folks and trying new things. Now it asks, would they be glad they went?</p></div>
  </div>

  <h3>The safety net</h3>
  <div class='cs-guards'>
    <div><b>Simple rules go first</b><p>Price, ticket, and topic rules run before any AI. They're cheap, predictable, and keep the obvious stuff out.</p></div>
    <div><b>No guessing</b><p>If an event is missing a date or a place, it waits for us with a note explaining why.</p></div>
    <div><b>The AI doesn't get the close calls</b><p>When it's not sure, we decide. One spammy pick costs more trust than one missed event.</p>
      <span class='rule'>{keep_at}+ goes on the list · {drop_below} to {keep_at - 1} comes to us · under {drop_below} is left off</span></div>
    <div><b>We always win</b><p>A thumbs up or down beats the AI's score right away, and our latest votes become examples it learns from.</p>
      <span class='rule'>our 12 most recent votes go into its instructions</span></div>
    <div><b>Bad weeks don't go live</b><p>If a run looks broken, it's held. Our followers keep seeing last week's list until we take a look.</p>
      <span class='rule'>held if events drop by half, most pages fail, sites go quiet, or it rejects 60%+</span></div>
    <div><b>Everything leaves a trail</b><p>Every skipped event keeps its reason, and new instructions mean every event gets re-judged.</p>
      <span class='rule'>nothing disappears without a note</span></div>
  </div>

  <h3>How we'll know it's working</h3>
  <div class='cs-metrics'>
    <div class='cs-metric'><b>{val(m.get('precision'))}</b><span>Picks we agree with</span><small>Of what the AI put on the list (precision)</small></div>
    <div class='cs-metric'><b>{val(m.get('recall'))}</b><span>Good events it caught</span><small>Of the events we'd pick (recall)</small></div>
    <div class='cs-metric'><b>{val(m.get('close_share'))}</b><span>Sent to us</span><small>Events it wasn't sure about</small></div>
    <div class='cs-metric'><b>{votes}</b><span>Votes so far</span><small>{'Enough to grade it' if votes >= 10 else 'We start grading at 10'}</small></div>
  </div>
</div></div></div>"""


def failures(keep_at: int = 70, drop_below: int = 40) -> str:
    cards = [
        ("Keywords missed the point", "\"Free AI Webinar: Grow Your Business 10x\" passed every rule. So did a revival night and a campaign event.",
         "I added an AI that reads for meaning, and kept the keyword rules as a quick first pass."),
        ("A site went quiet", "Greater Seattle on the Cheap started sending back nothing. No error, just a shorter list.",
         "Now a run gets held if sites go quiet, and we get a heads-up when even one usual site comes back empty."),
        ("Old news", "One site's main page was still showing last month's events. Everything looked fine and was totally out of date.",
         "It now reads that site's pages for this month and the next two."),
        ("Long pages got cut off", "Big listing pages were too long to read in one go, so events near the bottom disappeared.",
         "It reads long pages in overlapping pieces, so nothing falls through a gap."),
        ("\"Free\" wasn't always free", "Ticket links, cover charges, and prices buried in descriptions slipped right past us.",
         "I added rules for ticket language and dollar amounts, each with its own reason."),
        ("Our votes kept vanishing", "Every time the app restarted, our votes and filter changes were gone.",
         "Moved them into a real database (Supabase), so they stick."),
    ]
    c = "".join(f"<div class='cs-card'><span class='t'>{e(t)}</span><p>{e(p)}</p><div class='fix'>{e(f)}</div></div>"
                for t, p, f in cards)
    return f"""
<div class='cs'><div class='cs-sec'><div class='cs-num'>04</div><div>
  <h2>What <em>broke</em></h2>
  <p class='kicker'>Nothing crashed. Things went wrong quietly, like a shorter list or an old page, which is
  harder to catch. Here's what happened and what I changed.</p>
  <div class='cs-fail'>{c}</div>
  <h3>Where I kept people in charge</h3>
  <div class='cs-pivot'>
    <div><span class='lbl'>The agent handles</span><ul><li>Reading every site, every week</li><li>Cleanup and fact checks</li>
      <li>A first opinion on every event, with a reason</li><li>Holding a run that looks broken</li></ul></div>
    <div><span class='lbl'>We handle</span><ul><li>Every close call (scores {drop_below} to {keep_at - 1})</li><li>Deciding whether a held run goes live</li>
      <li>The graphic and the caption, because that's our voice</li><li>Client tracking. I built it, then paused it to focus on this.</li></ul></div>
  </div>
  <p class='cs-quote'>The AI never posts. It does the reading so we can do the choosing.</p>
  <div class='cs-end'>Coming up: a set of hand-picked test events every new version has to pass, tracking which picks people
  actually click, and a button that drops picks straight into our template.</div>
</div></div></div>"""
