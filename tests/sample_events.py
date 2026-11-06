"""A realistic extractor output, used by the tests and by `python demo.py`.

Includes the messy cases real listing pages produce: the same event on two
sites, a paid event, a past event, a missing venue, and an unreadable date.
"""
from datetime import date

TODAY = date(2026, 11, 4)  # a Wednesday

SAMPLE_EVENTS_RAW = [
    {"title": "Fremont Vintage Market", "date": "2026-11-08", "time": "10am",
     "venue": "Fremont Canal Park", "neighborhood": "Fremont", "cost": "Free",
     "description": "Over 100 vendors selling vintage clothes, vinyl, and handmade goods.",
     "link": "https://example.com/fremont-market", "source": "https://www.events12.com/seattle/"},
    {"title": "Fremont  Vintage Market!", "date": "November 8, 2026", "time": "",
     "venue": "Fremont Canal Park", "neighborhood": "", "cost": "free",
     "description": "", "link": "", "source": "https://do206.com/free-events-seattle"},
    {"title": "First Thursday Art Walk", "date": "2026-11-05", "time": "5pm",
     "venue": "Pioneer Square galleries", "neighborhood": "Pioneer Square", "cost": "Free",
     "description": "Gallery doors open late across Pioneer Square.",
     "link": "https://example.com/art-walk", "source": "https://everout.com/seattle/events/"},
    {"title": "DJs in a Dive Bar", "date": "2026-11-07", "time": "9pm",
     "venue": "Blue Moon Tavern", "neighborhood": "U District", "cost": "No cover",
     "description": "Three local DJs spin vinyl at a legendary dive bar.",
     "link": "https://example.com/blue-moon", "source": "https://do206.com/free-events-seattle"},
    {"title": "Discovery Park Trail Cleanup", "date": "2026-11-08", "time": "9am",
     "venue": "Discovery Park", "neighborhood": "Magnolia", "cost": "Free",
     "description": "Volunteer to clear trails, with coffee after.",
     "link": "https://example.com/cleanup", "source": "https://www.greaterseattleonthecheap.com/this-week/"},
    {"title": "Hidden Door Comedy", "date": "2026-11-06", "time": "8pm",
     "venue": "Aurora Ave N", "neighborhood": "Shoreline", "cost": "Free",
     "description": "New stand-up material behind an unmarked door.",
     "link": "https://example.com/comedy", "source": "https://everout.com/seattle/events/"},
    {"title": "Rooftop Sunset Yoga", "date": "2026-11-09", "time": "4pm",
     "venue": "Pike Place rooftop", "neighborhood": "Downtown", "cost": "Free",
     "description": "All levels yoga over Elliott Bay. Mats provided.",
     "link": "https://example.com/yoga", "source": "https://www.events12.com/seattle/"},
    {"title": "Film in the Library", "date": "2026-11-12", "time": "6pm",
     "venue": "Central Library", "neighborhood": "Downtown", "cost": "Free",
     "description": "A classic movie screening in the Microsoft Auditorium.",
     "link": "https://example.com/film", "source": "https://www.events12.com/seattle/"},
    {"title": "Holiday Tree Lighting", "date": "2026-11-27", "time": "5pm",
     "venue": "Westlake Center", "neighborhood": "Downtown", "cost": "Free",
     "description": "The downtown tree lights up with carolers and a countdown.",
     "link": "https://example.com/tree", "source": "https://www.events12.com/seattle/"},
    {"title": "Gingerbread Village Viewing", "date": "2026-12-05", "time": "11am",
     "venue": "Seattle Sheraton lobby", "neighborhood": "Downtown", "cost": "Free",
     "description": "Architects build a whole village out of gingerbread.",
     "link": "https://example.com/gingerbread", "source": "https://www.greaterseattleonthecheap.com/this-week/"},
    {"title": "Winterfest Ice Sculptures", "date": "2026-12-12", "time": "1pm",
     "venue": "Seattle Center Armory", "neighborhood": "Queen Anne", "cost": "Free",
     "description": "Live ice carving and a model train village.",
     "link": "https://example.com/winterfest", "source": "https://www.seattlecenter.com/events/event-calendar"},
    {"title": "Solstice Lantern Walk", "date": "2026-12-21", "time": "4:30pm",
     "venue": "Gas Works Park", "neighborhood": "Wallingford", "cost": "Free",
     "description": "Bring a lantern for a walk around the lake at dusk.",
     "link": "https://example.com/lanterns", "source": "https://everout.com/seattle/events/"},
    {"title": "Polar Bear Plunge", "date": "2027-01-01", "time": "12pm",
     "venue": "Matthews Beach Park", "neighborhood": "Lake City", "cost": "Free",
     "description": "Start the year with a jump into Lake Washington.",
     "link": "https://example.com/plunge", "source": "https://do206.com/free-events-seattle"},
    {"title": "MLK Day March and Rally", "date": "2027-01-18", "time": "9:30am",
     "venue": "Garfield High School", "neighborhood": "Central District", "cost": "Free",
     "description": "Workshops, a rally, and a march honoring Dr. King.",
     "link": "https://example.com/mlk", "source": "https://www.events12.com/seattle/"},
    # Free, with keywords that look alike, but very different intent:
    {"title": "Seattle AI Builders Meetup", "date": "2026-11-12", "time": "6pm",
     "venue": "Fremont Studios", "neighborhood": "Fremont", "cost": "Free",
     "description": "Community meetup with three lightning talks from local founders, then open networking.",
     "link": "https://example.com/ai-meetup", "source": "https://www.eventbrite.com/d/wa--seattle/free--events/"},
    {"title": "Free AI Webinar: Grow Your Business 10x", "date": "2026-11-13", "time": "12pm",
     "venue": "Online (Seattle)", "neighborhood": "", "cost": "Free",
     "description": "Learn the AI secrets top agencies use. Limited spots, book your free strategy call after.",
     "link": "https://example.com/webinar", "source": "https://www.eventbrite.com/d/wa--seattle/free--events/"},
    {"title": "Free Wealth Building Workshop", "date": "2026-11-14", "time": "10am",
     "venue": "Hotel conference room", "neighborhood": "Bellevue", "cost": "Free",
     "description": "Discover passive income strategies. Free lunch for attendees who complete a consultation.",
     "link": "https://example.com/wealth", "source": "https://everout.com/seattle/events/"},
    {"title": "Neighborhood Tool Library Open Hours", "date": "2026-11-15", "time": "11am",
     "venue": "Phinney Neighborhood Center", "neighborhood": "Phinney Ridge", "cost": "Free",
     "description": "Borrow tools, get help fixing small things, meet neighbors.",
     "link": "https://example.com/tools", "source": "https://do206.com/free-events-seattle"},
    {"title": "Sunday Revival Worship Night", "date": "2026-11-15", "time": "6pm",
     "venue": "Grace Fellowship Hall", "neighborhood": "Shoreline", "cost": "Free",
     "description": "An evening of worship and prayer. Bring a friend who needs to hear the message.",
     "link": "https://example.com/revival", "source": "https://everout.com/seattle/events/"},
    {"title": "Candidate Meet and Greet", "date": "2026-11-16", "time": "5pm",
     "venue": "Campaign office", "neighborhood": "Capitol Hill", "cost": "Free",
     "description": "Meet the candidate, sign up to volunteer, and learn how to get out the vote for our side.",
     "link": "https://example.com/candidate", "source": "https://do206.com/free-events-seattle"},
    {"title": "Diwali Festival of Lights", "date": "2026-11-08", "time": "12pm",
     "venue": "Seattle Center Armory", "neighborhood": "Queen Anne", "cost": "Free",
     "description": "Dance, food, and lantern making for the whole community.",
     "link": "https://example.com/diwali", "source": "https://www.seattlecenter.com/events/event-calendar"},
    # Cases that should go to review:
    {"title": "Seattle Symphony Open Rehearsal", "date": "2026-11-07", "time": "10am",
     "venue": "Benaroya Hall", "neighborhood": "Downtown", "cost": "$15",
     "description": "Watch the orchestra rehearse.", "link": "", "source": "https://www.events12.com/seattle/"},
    {"title": "Halloween Pumpkin Walk", "date": "2026-10-31", "time": "6pm",
     "venue": "Volunteer Park", "neighborhood": "Capitol Hill", "cost": "Free",
     "description": "Carved pumpkins line the paths.", "link": "", "source": "https://do206.com/free-events-seattle"},
    {"title": "Ballard Night Market", "date": "2026-11-14", "time": "5pm",
     "venue": "", "neighborhood": "Ballard", "cost": "Free",
     "description": "Food trucks and makers.", "link": "", "source": "https://everout.com/seattle/events/"},
    {"title": "Winter Lights Preview", "date": "sometime in December", "time": "",
     "venue": "Seattle Center", "neighborhood": "Queen Anne", "cost": "Free",
     "description": "", "link": "", "source": "https://www.seattlecenter.com/events/event-calendar"},
]


def sample_state(**settings) -> dict:
    """Pipeline state as if the retriever and extractor had just run on the samples."""
    import copy
    from collections import Counter

    events = copy.deepcopy(SAMPLE_EVENTS_RAW)
    for i, e in enumerate(events, 1):
        e["id"] = f"e{i:03d}"
    counts = Counter(e["source"] for e in events)
    pages = [{"url": u, "status": "read", "events": n} for u, n in counts.items()]
    pages.append({"url": "https://www.eventbrite.com/d/wa--seattle/free--events/",
                  "status": "could not load", "events": 0})
    return {"events_raw": events, "today": TODAY, "pages": pages, "curation": sample_curation(events),
            "feedback_rows": [],
            "source_urls": [p["url"] for p in pages],
            "pages_failed": [p["url"] for p in pages if p["status"] != "read"], **settings}


# What the classifier said about the samples, so the demo shows scores without API calls.
SAMPLE_SCORES = {
    "Fremont Vintage Market": ("Local business celebration", 86, "Big, well-loved local market with named location."),
    "First Thursday Art Walk": ("Arts and culture", 91, "Recurring neighborhood art walk, open to everyone."),
    "DJs in a Dive Bar": ("Arts and culture", 74, "Fun local night out, details are thin."),
    "Discovery Park Trail Cleanup": ("Outdoors and volunteering", 88, "Volunteer outdoors event with a clear host."),
    "Hidden Door Comedy": ("Arts and culture", 72, "Local comedy, a bit underground."),
    "Rooftop Sunset Yoga": ("Free class or talk", 68, "Nice class, but could be a studio promo."),
    "Film in the Library": ("Arts and culture", 80, "Free public screening at the library."),
    "Holiday Tree Lighting": ("Community gathering", 93, "Classic downtown community tradition."),
    "Gingerbread Village Viewing": ("Community gathering", 84, "Free seasonal display, family friendly."),
    "Winterfest Ice Sculptures": ("Arts and culture", 87, "Free live carving at Seattle Center."),
    "Solstice Lantern Walk": ("Community gathering", 82, "Community walk with a clear place and time."),
    "Polar Bear Plunge": ("Community gathering", 79, "Fun tradition, details are light."),
    "MLK Day March and Rally": ("Community gathering", 95, "Major community event with workshops and a march."),
    "Seattle AI Builders Meetup": ("High-value networking", 86, "Named community meetup with talks and networking."),
    "Free AI Webinar: Grow Your Business 10x": ("Marketing pitch", 14, "Online lead capture ending in a sales call."),
    "Free Wealth Building Workshop": ("Sales funnel", 9, "Free lunch in exchange for a sales consultation."),
    "Neighborhood Tool Library Open Hours": ("Community gathering", 58, "Useful and local, but low excitement."),
    "Sunday Revival Worship Night": ("Religious service", 8, "A worship service aimed at bringing in newcomers."),
    "Candidate Meet and Greet": ("Divisive or partisan", 6, "A campaign event recruiting volunteers for one side."),
    "Diwali Festival of Lights": ("Community gathering", 92, "Citywide cultural festival open to everyone."),
}


def sample_curation(events: list[dict]) -> dict:
    import filters
    from agents.normalizer import parse_date
    out = {}
    for e in events:
        hit = SAMPLE_SCORES.get(e["title"].strip())
        if hit:
            key = filters.event_key({"title": e["title"], "date": parse_date(e["date"])})
            out[key] = {"intent": hit[0], "score": hit[1], "reason": hit[2], "version": "sample"}
    return out
