# Seattle Unlocked event agent

Finding free events for Seattle Unlocked used to take about two hours every cycle. This pipeline does it in minutes: six agents read trusted listing sites, pull out each event, clean and check it, and write rows ready to drop into the events sheet that powers the website.

Every event either passes all checks or goes to a person for review with a written reason. Nothing is silently dropped.

## Who it's for

**Readers: the curious local.** Adults 28 to 52 in and around Seattle, Washington who are:

- **Outgoing:** like meeting new people and show up, often with a friend.
- **Community-minded:** want to know their neighbors and support local makers, artists, and causes.
- **Low-cost:** free first, and want real value, not a cheap teaser for something paid.
- **Adventurous:** try new neighborhoods, get outdoors, and say yes to first-time experiences.
- **Not interested in sales pitches:** they leave the moment an event turns into a pitch or a funnel.

They want a short list they can trust for this week. One salesy or vague pick loses them. The AI curator's instructions describe this same reader (`AUDIENCE` in `agents/curator.py`).

**The team** curates: reviews held events, votes, and confirms picks. **Brand clients** partner with Seattle Unlocked and see only the client view.

## How it works

```
retriever → extractor → normalizer → validator → reasoner → synthesizer
```

| Step | What it does |
|---|---|
| **Retriever** | Picks which listing pages to read: six trusted Seattle sites, plus matching pages from a search on those same sites. |
| **Extractor** | Reads each page and asks a model to list every event on it as structured data (title, date, time, venue, neighborhood, cost, description, link). |
| **Normalizer** | Cleans fields, reads dates in several formats, and merges the same event found on different sites, keeping the most detailed copy. |
| **Validator** | Checks each event: has a title and venue, a date it understands, falls in the next two weeks, and is free. Anything that fails goes to review with the reason. |
| **Reasoner** | Tags a category (Music, Art, Market, Outdoors...) and suggests picks: detailed, weekend events, at most two per category so the feature stays varied. |
| **Synthesizer** | Writes rows in the sheet's exact columns (`title, date, time, spot, hood, cat, desc, cost, link, pick`) and a short report. |

Suggested picks are only suggestions. A person confirms the `pick` column in the sheet, and the website features what's marked there.

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then add your OpenAI and Tavily keys

python demo.py         # sample events, no keys needed
python main.py         # live run: this week's free Seattle events
streamlit run app.py   # web view, with sample or live data
python -m pytest       # offline tests
```

`main.py` options: `--days 7`, `--picks 5`, `--pages 10`, `--include-paid`, `-v` for step-by-step logs. Results are saved to `output/events_<date>.csv`.

## Project layout

```
agents/       one file per step, plus clients.py for API clients
pipeline.py   wires the steps together with LangGraph
config.py     settings and trusted source pages
main.py       command line
app.py        Streamlit view
demo.py       sample run without keys
tests/        offline tests and sample data
```

## Notes

- Keys live only in `.env`, which git ignores. Nothing prints or logs them.
- If one page fails to load or the model returns something unreadable, that page is skipped and counted in the report. The rest of the run continues.

## Public page and team sign-in

The app has two views:

- **Public:** read-only. Anyone can browse the month tabs, available events, held events with their checks, and the full record. It shows the latest saved snapshot (`snapshots/latest.json`), so visitors never trigger API calls.
- **Team:** sign in with the team password (sidebar, "Team sign in") to run a live search, add events, edit picks, and download sheet rows. A live run also saves a new snapshot.

Until the first live run is saved, the public page shows sample events with a "Sample data" label.

## Deploy to Streamlit Community Cloud

1. Push this repo to GitHub (it can stay private).
2. At share.streamlit.io, sign in with GitHub and click **Create app**. Pick this repo, branch `main`, main file `app.py`. Under Advanced settings, choose Python 3.11.
3. In the app's **Settings > Secrets**, paste the values from `secrets.example.toml` with your real keys and a long team password.
4. Deploy. Share the app URL; give the team password only to people who should run and publish.

## Weekly refresh

`.github/workflows/refresh.yml` runs `refresh.py` every Monday, saves `snapshots/latest.json`, and commits it. Streamlit redeploys on the new commit, so the public page updates on its own.

Set it up once: in the GitHub repo, **Settings > Secrets and variables > Actions**, add `OPENAI_API_KEY` and `TAVILY_API_KEY`. To run it right away, open the **Actions** tab, pick "Weekly event refresh", and click **Run workflow**.

Note: events added in the app are saved on the server and reset when Streamlit restarts the app. Connecting the Google Sheet will make them permanent.

## Saving the team's work (Supabase)

Votes, filter rules, allowed events, the AI operating point, and hand-added events are saved to Supabase when `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` are set. Without them they go to `data/`, which Streamlit Cloud wipes on every restart. Signed-in team members see which one is active in the sidebar.

1. Create a free project at supabase.com.
2. SQL editor > New query > paste `sql/schema.sql` > Run.
3. Project settings > API Keys: copy the project URL and the **secret** (or legacy `service_role`) key. Never the publishable / anon key, and never commit it.
4. Put both in `.env`, then run `python check_supabase.py`. It checks the tables, tests a write, and copies up anything saved locally.
5. Add both to Streamlit secrets and to GitHub Actions secrets.

## Client tracker

The **Clients** page shows every client and where each deal stands:

- **Client types:** Large business, Small business, Team member (new senders start as "Unsorted" unless a hint matches).
- **Deal stages:** 1 Unconfirmed deal, 2 Awaiting client approval, 3 Completed, awaiting invoice, 4 Fully complete.
- **Public view:** the pipeline board, counts by type, and emails per week. Names, emails, and deal titles are replaced with labels like "Large business · C-4F2A". Deal values are never shown.
- **Team view (signed in):** real names, sort new clients, move deals between stages, add clients by hand, and "Sync Gmail now."

Until Supabase is connected it shows made-up sample clients, labeled as sample.

### Set up (about 20 minutes, once)

1. **Supabase:** in your project, open the SQL editor and run `crm/schema.sql`. Copy the project URL and the `service_role` key (Project settings > API).
2. **Gmail:** in Google Cloud console, create a project, enable the Gmail API, create an OAuth client of type "Desktop app," and download its JSON. Then on your Mac:
   ```bash
   python -m crm.gmail_auth ~/Downloads/client_secret.json
   ```
   Sign in to the inbox clients email. It prints one line of JSON: that's `GMAIL_TOKEN_JSON`. Access is read-only.
3. **In Gmail,** make a label called `Clients` and a filter that applies it to client emails (or set `GMAIL_QUERY` to any Gmail search).
4. **Secrets:** add `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, and `GMAIL_TOKEN_JSON` to Streamlit secrets and to GitHub Actions secrets. Optional hints go in GitHub Actions variables: `GMAIL_SELF`, `TEAM_EMAILS`, `TEAM_DOMAINS`, `LARGE_CLIENT_DOMAINS`.
5. **Hourly sync:** move `setup/clients-sync.yml` to `.github/workflows/`. Run it once from the Actions tab.

## AI curation and the feedback loop

Keyword rules (price, tickets, blocked topics) run first as cheap guardrails. Then an LLM curator (`agents/curator.py`) reads each remaining event and returns an **intent** (community gathering, high-value networking, marketing pitch, sales funnel...), a **0-100 relevance score**, and a one-line reason. It judges meaning, not keywords: a community "AI meetup" with named talks scores high; a free "AI webinar" that ends in a sales call scores low.

**Operating point.** Score at or above `keep_at` (70) goes on the list; below `drop_below` (40) is filtered as "AI: low relevance"; in between is held for a person. The public list is tuned for precision; the review band protects recall. The team changes the band on the **AI curation** page.

**Feedback loop.** Signed-in team members get thumbs up / down on every event. A vote overrides the model immediately, is saved (Supabase `feedback` table, or `data/feedback.json`), and the most recent votes are added to the classifier's instructions as few-shot examples on its next run. Votes double as labels: the AI curation page plots precision and recall against them at every threshold.

**Cost.** Scores are cached by event in the snapshot, so each event is classified once. Only `refresh.py`, "Run live search", and "Re-curate with AI" call the model.
