# Seattle Unlocked event agent

Finding free events for Seattle Unlocked used to take about two hours every cycle. This pipeline does it in minutes: six agents read trusted listing sites, pull out each event, clean and check it, and write rows ready to drop into the events sheet that powers the website.

Every event either passes all checks or goes to a person for review with a written reason. Nothing is silently dropped.

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
