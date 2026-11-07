"""Step 5: semantic curation. An LLM judges each event's intent and value.

Keyword rules (filters.py) still run first as cheap guardrails: anything with a
price or a blocked topic never reaches the model. This step handles what
keywords can't, like telling a real community "AI meetup" from an "AI webinar"
that exists to sell something.

Each event gets:
  intent   one of INTENTS
  score    0-100, how worth featuring it is for Seattle Unlocked's audience
  reason   one short sentence

Then the operating point decides what happens:
  score >= keep_at      stays on the list
  drop_below..keep_at   held for a person to review (the model isn't sure)
  score <  drop_below   filtered out as "AI: low relevance"

We tune for precision on the public list (a bad pick costs reader trust) and
protect recall with the review band (borderline events reach a person instead
of being dropped). Team thumbs override the model and feed back into the prompt.

Results are cached by event key, so the app never pays to classify the same
event twice. Only refresh.py and the team's "Re-curate" button call the model.
"""
import json
import logging

import feedback
from config import CURATOR_MODEL

log = logging.getLogger(__name__)

PROMPT_VERSION = "curator-v3"
BATCH = 20

# Who we curate for. The app's AI curation page and the README describe the same reader.
AUDIENCE = {
    "name": "The curious local",
    "who": "Adults 28 to 52 who live in or around Seattle, Washington.",
    "traits": [
        ("Outgoing", "Likes meeting new people and shows up, often with a friend."),
        ("Community-minded", "Wants to know their neighbors and support local makers, artists, and causes."),
        ("Low-cost", "Free first. Wants real value, not a cheap teaser for something paid."),
        ("Adventurous", "Tries new neighborhoods, gets outdoors, says yes to first-time experiences."),
        ("No sales pitches", "Leaves the moment an event turns into a pitch, a demo, or a sign-up funnel."),
    ],
    "wants": "A short list they can trust for this week, with enough detail to just go.",
    "loses_them": "One salesy or vague pick. Events built mainly for young kids or for college students are a weaker fit.",
}

INTENTS = [
    "Community gathering",
    "Arts and culture",
    "Outdoors and volunteering",
    "Free class or talk",
    "High-value networking",
    "Local business celebration",
    "Marketing pitch",
    "Sales funnel",
    "Vague or low effort",
    "Not open to the public",
    "Religious service",
    "Divisive or partisan",
]
LOW_VALUE = {"Marketing pitch", "Sales funnel", "Vague or low effort", "Not open to the public",
             "Religious service", "Divisive or partisan"}

SYSTEM = """You curate free events for Seattle Unlocked, a guide about 80,000 Seattle locals trust \
to find free things genuinely worth leaving the house for. What we stand for: community. \
Events where neighbors meet, make, celebrate, learn, or help out together, with nothing to sell.

Who you are choosing for: adults 28 to 52 in and around Seattle who are outgoing, community-minded, \
low-cost, and adventurous. They love meeting people, exploring new neighborhoods, getting outdoors, and \
trying things for the first time. They have no patience for sales pitches. Ask of every event: would this \
person be glad they went? Events built mainly for young kids or for college students are a weaker fit \
(family events adults also enjoy are fine).

Judge each event on its intent and value to a curious local, not on keywords.
The same words can mean very different things: a community "AI meetup" with named \
hosts and talks is high-value networking; a free "AI webinar" that ends in a product \
demo is a marketing pitch. A free "wealth workshop" or "free consultation" is usually \
a sales funnel.

Score highest: events whose main purpose is bringing people together. Festivals, markets, \
art walks, volunteering, cleanups, potlucks, neighborhood celebrations, free classes taught \
for their own sake, and meetups with a clear host and agenda.

Score low, even when free:
- Salesy: the event mainly exists to sell, collect leads, recruit, or upsell (free \
  seminars, consultations, "limited spots" webinars, demos, multi-level marketing).
- Religious services: worship services, revivals, prayer meetings, Bible or scripture study, \
  or events meant to bring people into a faith. Cultural festivals with religious roots that \
  the whole community celebrates (Diwali, Lunar New Year, Day of the Dead, a holiday tree \
  lighting, a holiday market) are community events, not religious services, and are fine.
- Divisive or partisan: campaign events, events for or against a candidate or party, protests \
  or rallies on hot-button issues, and debates built around a deeply divisive topic. Treat every \
  side the same way. Widely shared civic commemorations (MLK Day, Veterans Day, Juneteenth \
  celebrations) and nonpartisan civic events (voter registration, a library talk) are fine.
- Also low: vague details, online only, members or invite only, outside the Seattle area.

Score 0-100:
  80-100 clearly worth featuring
  50-79  maybe, a person should look
  0-49   do not feature

Intent must be exactly one of: {intents}.

Return JSON: {{"results": [{{"key": "...", "intent": "...", "score": 0, "reason": "one short sentence"}}]}}
with one result for every event you are given, using its key."""


def _payload(e: dict) -> dict:
    return {
        "key": e["key"],
        "title": e.get("title", ""),
        "description": (e.get("description") or "")[:400],
        "venue": e.get("venue", ""),
        "neighborhood": e.get("neighborhood", ""),
        "cost": e.get("cost", ""),
        "source": e.get("source", ""),
    }


def build_messages(events: list[dict], examples: list[dict]) -> list[dict]:
    system = SYSTEM.format(intents=", ".join(INTENTS))
    shots = feedback.few_shot_text(examples)
    if shots:
        system += "\n\n" + shots
    return [{"role": "system", "content": system},
            {"role": "user", "content": json.dumps({"events": [_payload(e) for e in events]})}]


def parse(raw: str, keys: list[str]) -> dict[str, dict]:
    """Model reply -> {key: {intent, score, reason}}. Bad or missing rows are skipped."""
    try:
        rows = json.loads(raw).get("results", [])
    except (json.JSONDecodeError, AttributeError, TypeError):
        return {}
    out = {}
    for r in rows if isinstance(rows, list) else []:
        if not isinstance(r, dict) or r.get("key") not in keys:
            continue
        try:
            score = max(0, min(100, int(r.get("score"))))
        except (TypeError, ValueError):
            continue
        intent = r.get("intent") if r.get("intent") in INTENTS else "Vague or low effort"
        out[r["key"]] = {"intent": intent, "score": score, "reason": str(r.get("reason") or "")[:160],
                         "version": PROMPT_VERSION}
    return out


def classify_batch(events: list[dict], examples: list[dict]) -> dict[str, dict]:
    """One model call for up to BATCH events."""
    from agents import clients
    reply = clients.openai().chat.completions.create(
        model=CURATOR_MODEL, temperature=0, response_format={"type": "json_object"},
        messages=build_messages(events, examples))
    return parse(reply.choices[0].message.content, [e["key"] for e in events])


def curate(state: dict) -> dict:
    import filters

    events = state.get("events_valid", [])
    for e in events:
        e["key"] = e.get("key") or filters.event_key(e)
    cache: dict = dict(state.get("curation") or {})
    rows = state["feedback_rows"] if "feedback_rows" in state else feedback.load()
    votes = feedback.votes_by_key(rows)
    # Events the team allowed on the Filters page count as approved here too.
    for k in (state.get("filters") or filters.load()).get("allow", []):
        votes.setdefault(k, 1)

    # Call the model only for events it hasn't seen, and only when allowed.
    def stale(k):  # never scored, or scored by an older version of the instructions
        c = cache.get(k)
        return c is None or c.get("version") not in (PROMPT_VERSION, "sample")
    todo = [e for e in events if stale(e["key"]) and not e.get("custom")]
    if state.get("curate_live") and todo:
        examples = feedback.few_shots(rows)
        for i in range(0, len(todo), BATCH):
            batch = todo[i:i + BATCH]
            try:
                cache.update(classify_batch(batch, examples))
            except RuntimeError:
                raise  # setup problems stop the run with a clear message
            except Exception as err:
                log.warning("Curator: batch %d failed: %s", i // BATCH, err)
    state["curation"] = cache

    keep_at = state.get("keep_at", 70)
    drop_below = state.get("drop_below", 40)
    kept, review, filtered = [], list(state.get("events_review", [])), list(state.get("events_filtered", []))
    for e in events:
        c = cache.get(e["key"])
        e["ai"] = c
        v = votes.get(e["key"])
        if v == 1:
            e["ai_decision"] = "approved by team"
            kept.append(e)
        elif v == -1:
            filtered.append({**e, "filter_category": "Downvoted by team",
                             "filter_reason": "downvoted by team: " + (c["reason"] if c else "no note"),
                             "filter_key": e["key"]})
        elif e.get("custom") or c is None:
            e["ai_decision"] = "added by you" if e.get("custom") else "not curated yet"
            kept.append(e)
        elif c["score"] >= keep_at:
            e["ai_decision"] = f"AI {c['score']}: {c['reason']}"
            kept.append(e)
        elif c["score"] >= drop_below:
            review.append({**e, "review_reasons": [f"AI unsure ({c['score']}): {c['reason']}"]})
        else:
            filtered.append({**e, "filter_category": "AI: low relevance",
                             "filter_reason": f"ai {c['intent'].lower()} ({c['score']}): {c['reason']}",
                             "filter_key": e["key"]})
    state["events_valid"], state["events_review"], state["events_filtered"] = kept, review, filtered
    return state
