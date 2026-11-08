"""All app-wide CSS in one place. Page-specific CSS that lives inside iframes stays with its component."""
import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700&family=Bodoni+Moda:ital,opsz,wght@0,6..96,400;1,6..96,400&family=Hanken+Grotesk:wght@400;500&display=swap');
/* Look: light and quiet like Stripe, warmer and softer. Warm white, plum accent, sage for good, coral for held. */
:root{--bg:#FBF9F7;--panel:#FFFFFF;--panel2:#F6F2EF;--line:#ECE6E1;--line2:#E2DAD4;
      --text:#2A2433;--dim:#6E6676;--muted:#706877;
      --blue:#A04D74;--blue-bg:rgba(160,77,116,.09);
      --green:#456F5E;--green-bg:rgba(94,140,122,.12);
      --red:#B14A40;--red-bg:rgba(194,86,75,.09);
      --orange:#8F6214;--mono:'Figtree',-apple-system,'Segoe UI',sans-serif;
      --shadow:0 1px 2px rgba(42,36,51,.04),0 2px 8px rgba(42,36,51,.04)}
html, body, .stApp, .stMarkdown p, label, input, textarea, button p {font-family:'Figtree',-apple-system,'Segoe UI',sans-serif}
.stApp{background:var(--bg)}
.block-container{padding-top:3.4rem;max-width:1160px}
.ob, .ob *, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label{font-family:'Figtree',-apple-system,'Segoe UI',sans-serif !important}

/* sidebar */
[data-testid="stSidebar"]{background:#F6F2EF;border-right:1px solid var(--line)}
[data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span{color:var(--dim)}
[data-testid="stSidebar"] button{border-radius:8px;box-shadow:none}
[data-testid="stSidebar"] button[kind="primary"]{background:var(--blue);border-color:var(--blue)}
[data-testid="stSidebar"] button[kind="primary"] p{color:#fff;font-weight:600}
[data-testid="stSidebar"] button[kind="secondary"]{background:#fff;border:1px solid var(--line2)}
[data-testid="stSidebar"] button[kind="secondary"] p{color:var(--text)}
.ob-brand{font-size:15px;font-weight:700;color:var(--text);display:flex;align-items:center;gap:9px;letter-spacing:-.01em}
.ob-brand i{display:inline-block;width:20px;height:20px;border-radius:50%;
            background:radial-gradient(circle at 35% 35%,#E7B3C8,#A04D74)}
.st-key-nav{margin-top:18px}
.st-key-nav button{justify-content:flex-start;min-height:36px;padding-left:12px;border:none !important;background:transparent !important}
.st-key-nav button > div, .st-key-nav button [data-testid="stMarkdownContainer"]{justify-content:flex-start;text-align:left;width:100%}
.st-key-nav button p{font-size:15px;font-weight:500;color:var(--text) !important}
.st-key-nav button:hover{background:rgba(42,36,51,.05) !important}
.st-key-nav button[kind="primary"]{background:var(--blue-bg) !important}
.st-key-nav button[kind="primary"] p{color:var(--blue) !important;font-weight:600}
.st-key-nav-months{padding-left:12px;border-left:1px solid var(--line2);margin:2px 0 6px 14px}
.st-key-nav-months button{min-height:30px}
.st-key-nav-months button p{font-size:14px !important;font-weight:400 !important;color:var(--dim) !important}
.st-key-nav-months button[kind="primary"] p{color:var(--blue) !important;font-weight:600 !important}
.st-key-nav-months [data-testid="stVerticalBlock"]{gap:2px}

/* page title */
.ob-title{padding:4px 0 22px;margin-bottom:22px;border-bottom:1px solid var(--line)}
.ob-title h1{font-size:38px;font-weight:700;letter-spacing:-.025em;color:var(--text);margin:0;padding:0;line-height:1.1}
.ob-title p{font-size:16px;color:var(--dim);margin:8px 0 0;max-width:62ch;line-height:1.5}
.ob-head{display:flex;align-items:baseline;gap:12px;margin:4px 0 16px}
.ob-head h2{font-size:24px;font-weight:700;letter-spacing:-.015em;color:var(--text);margin:0;padding:0}
.ob-type{font-size:13px;color:var(--muted)}
.ob-crumb{font-size:13px;color:var(--muted)}

/* stat cards */
.ob-stats{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:12px}
.ob-stat{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px;box-shadow:var(--shadow)}
.ob-stat span{display:block;font-size:13px;font-weight:500;color:var(--dim)}
.ob-stat b{display:block;font-size:26px;font-weight:700;letter-spacing:-.02em;color:var(--text);margin-top:4px;font-variant-numeric:tabular-nums}
.ob-stat.blue b{color:var(--blue)}.ob-stat.red b{color:var(--red)}.ob-stat.green b{color:var(--green)}
a.ob-stat.link{text-decoration:none;display:block;cursor:pointer}
a.ob-stat.link:hover{border-color:var(--orange)}
a.ob-stat.link b{color:var(--orange)}

/* sections: a plain heading, then a white card */
.ob-sec{display:flex;align-items:baseline;gap:8px;margin:34px 0 10px;padding:0;background:none;border:none}
.ob-sec .t{font-size:18px;font-weight:700;letter-spacing:-.01em;color:var(--text)}
.ob-sec .c{font-size:14px;color:var(--muted)}
.ob-sec .dot{display:none}
.ob-sec .hint{margin-left:auto;font-size:13px;color:var(--muted);font-weight:400}
.ob-list{border:1px solid var(--line);border-radius:12px;background:var(--panel);box-shadow:var(--shadow);overflow:hidden}
.ob-acc{margin-top:0}
.ob-acc > summary{list-style:none;cursor:pointer;user-select:none}
.ob-acc > summary::-webkit-details-marker, .ob-acc-day > summary::-webkit-details-marker{display:none}
.ob-acc-day > summary{list-style:none;cursor:pointer;user-select:none}
.ob-acc-day > summary:hover{background:#F8F4F1}
.chev{display:inline-block;width:0;height:0;border-left:5px solid var(--muted);border-top:4px solid transparent;
      border-bottom:4px solid transparent;margin-right:4px;transition:transform .15s}
details[open] > summary .chev{transform:rotate(90deg)}
.ob-empty-in{color:var(--muted);font-size:14px;padding:16px}
.empty{color:var(--dim);font-size:14px;padding:16px;border:1px solid var(--line);border-radius:12px;background:var(--panel)}

/* day headers */
.ob-day{display:flex;align-items:center;gap:10px;font-size:16px;font-weight:600;color:var(--text);
        padding:12px 16px;background:#FCFAF8;border-top:1px solid var(--line)}
.ob-acc-day:first-child .ob-day{border-top:none}
.ob-day .wd{font-size:13px;font-weight:600;color:var(--blue);background:var(--blue-bg);padding:2px 9px;border-radius:999px}
.ob-day .n{margin-left:auto;font-size:13px;font-weight:400;color:var(--muted)}
.ob-day.weekend .wd{color:var(--green);background:var(--green-bg)}
.ob-day.filt .wd{color:var(--orange);background:rgba(176,122,34,.1)}

/* event rows */
.ob-row{display:grid;grid-template-columns:32px minmax(0,1fr) auto;gap:14px;align-items:start;padding:14px 16px;
        border-top:1px solid var(--line);background:var(--panel)}
.ob-row:hover{background:#FDFBFA}
.ob-ic{width:32px;height:32px;border-radius:10px;background:var(--blue-bg);display:grid;place-items:center}
.ob-ic svg{width:16px;height:16px;fill:none;stroke:var(--blue);stroke-width:1.6}
.ob-ic.mine{background:var(--green-bg)}.ob-ic.mine svg{stroke:var(--green)}
.ob-ic.held{background:var(--red-bg)}.ob-ic.held svg{stroke:var(--red)}
.ob-t{font-size:16px;font-weight:600;color:var(--text);line-height:1.4}
.ob-t a{color:var(--text);text-decoration:none}.ob-t a:hover{color:var(--blue)}
.ob-props{display:flex;flex-wrap:wrap;gap:2px 16px;margin-top:4px;font-size:14px;color:var(--dim);line-height:1.5}
.ob-props i{font-style:normal;color:var(--muted);margin-right:5px}
.ob-props .ai-why{color:var(--dim);font-style:italic}
.ob-r{font-size:13px;color:var(--muted);white-space:nowrap;padding-top:3px}

/* tags and chips */
.tag{display:inline-block;font-size:12px;font-weight:500;padding:2px 9px;margin-left:8px;border-radius:999px;vertical-align:2px}
.tag.cat{background:var(--panel2);color:var(--dim)}
.tag.pick{background:var(--blue);color:#fff}
.tag.mine{background:var(--green-bg);color:var(--green)}
.tag.ai{font-size:12px}
.tag.ai.hi{background:var(--green-bg);color:var(--green)}
.tag.ai.mid{background:rgba(176,122,34,.1);color:var(--orange)}
.tag.ai.lo{background:var(--red-bg);color:var(--red)}
.chk{display:inline-block;font-size:12px;padding:2px 9px;margin:8px 4px 0 0;border-radius:999px}
.chk.ok{background:var(--green-bg);color:var(--green)}
.chk.no{background:var(--red-bg);color:var(--red)}
.chk-why{font-size:13px;color:var(--red);margin-left:6px}
.src-chips{display:flex;flex-wrap:wrap;gap:6px;padding:0 0 10px}
.src-chips span{font-size:13px;background:var(--panel);border:1px solid var(--line);padding:3px 10px;border-radius:999px;color:var(--dim)}
.src-chips b{color:var(--text);font-weight:600;margin-left:6px}
.rule-chips span{display:inline-block;font-size:13px;background:var(--panel);border:1px solid var(--line);color:var(--dim);
  padding:3px 10px;border-radius:999px;margin:0 4px 4px 0}
.ob-note{font-size:13px;color:var(--orange);background:rgba(176,122,34,.08);border:1px solid rgba(176,122,34,.2);
         border-radius:999px;padding:5px 12px;margin-bottom:12px;display:inline-block}

/* streamlit widgets */
[data-testid="stExpander"] details{border:1px solid var(--line);border-radius:12px;background:var(--panel);box-shadow:var(--shadow)}
[data-testid="stExpander"] summary p{font-weight:600;font-size:15px}
[data-testid="stDataFrame"]{border-radius:12px;overflow:hidden}
.st-key-teamlist [data-testid="stVerticalBlock"]{gap:0}

/* curation policy */
.policy{border:1px solid var(--line);border-radius:14px;background:var(--panel);box-shadow:var(--shadow);margin-bottom:24px;overflow:hidden}
.pol-k{display:block;font-size:14px;font-weight:600;color:var(--dim);margin-bottom:8px}
.pol-mission{padding:24px 26px;border-bottom:1px solid var(--line);background:linear-gradient(180deg,#FBF3F6,#FFFFFF)}
.pol-mission p{font-size:20px;line-height:1.5;color:var(--text);margin:0;max-width:60ch;letter-spacing:-.005em}
.pol-mission b{color:var(--blue);font-weight:600}
.pol-grid{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr)}
.pol-col{padding:20px 26px}
.pol-col.good{border-right:1px solid var(--line)}
.pol-col.good .pol-k{color:var(--green)}
.pol-col.bad .pol-k{color:var(--red)}
.pol-sub{font-size:15px;color:var(--dim);margin:0 0 12px;line-height:1.5}
.pol-chips{display:flex;flex-wrap:wrap;gap:6px}
.pol-chips span{font-size:14px;padding:4px 12px;border-radius:999px;background:var(--green-bg);color:var(--green)}
.pol-avoid{padding:10px 0;border-top:1px solid var(--line)}
.pol-avoid:first-of-type{border-top:none;padding-top:0}
.pol-avoid b{font-size:15px;color:var(--text)}
.pol-avoid p{font-size:14px;color:var(--dim);margin:3px 0 0;line-height:1.55}
.pol-foot{padding:16px 26px;border-top:1px solid var(--line);display:grid;gap:8px;background:#FCFAF8}
.pol-foot p{font-size:14px;color:var(--dim);margin:0;line-height:1.6}
.pol-foot b{color:var(--text);font-weight:600}
@media (max-width:900px){.pol-grid{grid-template-columns:1fr}.pol-col.good{border-right:none;border-bottom:1px solid var(--line)}
  .ob-stats{grid-template-columns:repeat(2,minmax(0,1fr))}}
.teach{border:1px dashed var(--line2);border-radius:12px;background:var(--panel);padding:20px 22px;max-width:760px}
.teach p{font-size:15px;color:var(--dim);line-height:1.6;margin:0 0 10px}
.teach p.teach-lead{font-size:17px;font-weight:600;color:var(--text);margin-bottom:6px}
.teach b{color:var(--text);font-weight:600}
.teach-bar{height:8px;border-radius:999px;background:var(--panel2);overflow:hidden;margin:14px 0 6px}
.teach-bar i{display:block;height:100%;background:var(--blue);border-radius:999px}
.teach p.teach-count{font-size:14px;color:var(--dim);margin:0}
.teach-ex{padding:10px 0;border-top:1px solid var(--line);font-size:15px;color:var(--text)}
.teach-ex .chk{margin:0 8px 0 0}
.teach-why{display:block;font-size:14px;color:var(--dim);margin-top:4px}
.teach p.teach-foot{font-size:13px;color:var(--muted);margin:10px 0 0}
.audience{border:1px solid var(--line);border-radius:14px;background:var(--panel);box-shadow:var(--shadow);
  padding:22px 26px;margin-bottom:18px}
.audience h3{font-size:24px;font-weight:700;letter-spacing:-.015em;color:var(--text);margin:0;padding:0}
.audience .aud-who{font-size:16px;color:var(--dim);margin:4px 0 16px}
.aud-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px}
.aud-t{background:var(--blue-bg);border-radius:10px;padding:12px 14px}
.aud-t b{font-size:15px;color:var(--blue)}
.aud-t p{font-size:14px;color:var(--text);margin:4px 0 0;line-height:1.5}
.aud-foot{margin-top:14px;display:grid;gap:4px}
.aud-foot p{font-size:15px;color:var(--dim);margin:0;line-height:1.55}
.aud-foot b{color:var(--text);font-weight:600}
@media (max-width:900px){.aud-grid{grid-template-columns:1fr 1fr}}
.aud-line{display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin:0;font-size:14px;color:var(--dim)}
.aud-line .aud-k{color:var(--muted);margin-right:2px}
.aud-line b{color:var(--text);font-weight:600;margin-right:4px}
.aud-line span:not(.aud-k){background:var(--blue-bg);color:var(--blue);padding:3px 10px;border-radius:999px;font-size:13px}
.breaker{border:1px solid rgba(177,74,64,.3);background:var(--red-bg);border-radius:12px;padding:16px 20px;margin-bottom:12px}
.breaker p{font-size:15px;color:var(--text);margin:0 0 6px;line-height:1.5}
.breaker p.br-lead{font-weight:700;color:var(--red);font-size:16px}
.breaker ul{margin:4px 0 8px 18px;padding:0}.breaker li{font-size:15px;color:var(--text);line-height:1.6}
.breaker p.br-meta{font-size:13px;color:var(--dim);margin:0}
.steps{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-bottom:14px}
.step{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px;display:grid;gap:4px;align-content:start}
.step .sn{width:26px;height:26px;border-radius:50%;background:var(--blue-bg);color:var(--blue);font-weight:700;
  font-size:14px;display:grid;place-items:center;margin-bottom:4px}
.step b{font-size:16px;color:var(--text)}
.step p{font-size:14px;color:var(--dim);margin:0;line-height:1.5}
.band{display:flex;gap:4px;border-radius:12px;overflow:hidden}
.band .seg{padding:12px 14px;min-width:0;display:grid;gap:2px}
.band .seg b{font-size:24px;font-weight:700;line-height:1.1}
.band .seg span{font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.band .lo{background:var(--red-bg)}.band .lo b,.band .lo span{color:var(--red)}
.band .mid{background:rgba(143,98,20,.1)}.band .mid b,.band .mid span{color:var(--orange)}
.band .hi{background:var(--green-bg)}.band .hi b,.band .hi span{color:var(--green)}
.aud-line{margin:0}
.venn-wrap{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(0,1fr);gap:28px;align-items:center;
  background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:20px 24px}
.venn svg{width:100%;max-width:520px;height:auto;display:block;margin:0 auto}
.venn-side{display:grid;gap:18px}
.vs-k{display:block;font-size:14px;font-weight:600;color:var(--dim);margin-bottom:8px}
.vs-k.never{color:var(--red)}.vs-k.ok{color:var(--green)}
.vs-chips{display:flex;flex-wrap:wrap;gap:6px}
.vs-chips span{font-size:14px;padding:4px 12px;border-radius:999px}
.vs-chips.never span{background:var(--red-bg);color:var(--red)}
.vs-chips.ok span{background:var(--green-bg);color:var(--green)}
.vs-block p{font-size:14px;color:var(--dim);margin:6px 0 0;line-height:1.5}
@media (max-width:900px){.steps,.venn-wrap{grid-template-columns:1fr}}
.cute h1, .ob-sec.cute .t{font-family:'Bodoni Moda',Didot,Georgia,serif !important;font-style:italic;font-weight:400;font-size:30px;letter-spacing:0;color:#1E2A47}
.ob-sec.cute{margin-top:44px}
.journey{display:grid;gap:18px;margin:6px 0 10px;position:relative}
.j-step{display:grid;grid-template-columns:minmax(0,300px) minmax(0,1fr);gap:28px;align-items:center;
  background:var(--panel);border:1px solid var(--line);border-radius:22px;padding:14px 28px 14px 14px;box-shadow:var(--shadow)}
.j-step.flip{grid-template-columns:minmax(0,1fr) minmax(0,300px);padding:14px 14px 14px 28px}
.j-step.flip .j-art{order:2}
.j-art svg{width:100%;height:auto;display:block;border-radius:18px}
.j-txt{display:grid;gap:6px;justify-items:start}
.j-n{width:30px;height:30px;border-radius:50%;background:var(--blue);color:#fff;font:600 15px 'Fredoka',sans-serif;
  display:grid;place-items:center}
.journey h3{font-size:24px;color:var(--text);margin:2px 0 0;padding:0;line-height:1.2}
.j-txt p{font-size:16px;color:var(--dim);margin:0;line-height:1.5;max-width:46ch}
.j-chip{margin-top:4px;font-size:13px;font-weight:600;color:var(--blue);background:var(--blue-bg);padding:4px 12px;border-radius:999px}
@media (max-width:760px){.j-step,.j-step.flip{grid-template-columns:1fr;padding:14px}.j-step.flip .j-art{order:0}}
</style>
"""


def inject() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
