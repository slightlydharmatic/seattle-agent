"""Made-up clients for demos and tests. Shown with a 'Sample data' label, never as real."""
from crm.model import STAGES

SAMPLE = [
    # name, email, type, deal title, stage, emails (subject, iso date)
    ("Avery Lin", "avery@northpoint-hotels.com", "Large business", "Holiday market feature", STAGES[0],
     [("Partnership inquiry", "2026-11-02T10:00:00+00:00")]),
    ("Jordan Park", "jordan@summitarena.com", "Large business", "Monthly round-up sponsor", STAGES[1],
     [("Sponsorship rates?", "2026-10-21T15:00:00+00:00"), ("Re: proposal", "2026-10-29T18:00:00+00:00")]),
    ("Sam Okafor", "sam.okafor@gmail.com", "Small business", "Custom story post", STAGES[2],
     [("Can you post our pop-up?", "2026-10-14T12:00:00+00:00"), ("Approved!", "2026-10-20T09:00:00+00:00")]),
    ("Riley Chen", "riley@fremontcoffee.co", "Small business", "Feed post", STAGES[3],
     [("Feed post for our anniversary", "2026-09-30T17:00:00+00:00"), ("Paid, thanks", "2026-10-12T11:00:00+00:00")]),
    ("Morgan Diaz", "morgan@lakeside-events.com", "Large business", "Event series", STAGES[0],
     [("Free event series", "2026-11-04T16:00:00+00:00")]),
    ("Casey Tran", "casey@studio-tran.com", "Small business", "Newsletter feature", STAGES[1],
     [("Newsletter feature", "2026-10-27T14:00:00+00:00")]),
    ("Taylor Brooks", "taylor@seattleunlocked.team", "Team member", "", None,
     [("Weekly content plan", "2026-11-03T08:00:00+00:00")]),
]


def sample_db() -> dict:
    clients, deals, emails = [], [], []
    for i, (name, email, ctype, title, stage, mails) in enumerate(SAMPLE, 1):
        cid = f"sample-{i}"
        clients.append({"id": cid, "name": name, "email": email, "company": "", "client_type": ctype,
                        "created_at": mails[0][1]})
        if title:
            deals.append({"id": f"deal-{i}", "client_id": cid, "title": title, "stage": stage, "notes": "",
                          "created_at": mails[0][1], "updated_at": mails[-1][1]})
        for j, (subj, when) in enumerate(mails):
            emails.append({"id": f"em-{i}-{j}", "client_id": cid, "gmail_id": f"g-{i}-{j}", "subject": subj,
                           "received_at": when, "snippet": ""})
    return {"clients": clients, "deals": deals, "emails": emails}
