"""Client tracker tests: no Supabase or Gmail needed."""
from crm import store as crm
from crm.model import STAGES, UNSORTED, masked, suggest_type
from crm.view import build_rows, card


def make_store(tmp_path):
    return crm.LocalStore(tmp_path / "crm.json")


def test_a_new_sender_becomes_a_client_with_a_stage_1_deal(tmp_path):
    s = make_store(tmp_path)
    assert crm.record_email(s, "Ana Ruiz <Ana@CBRE.com>", "g1", "Sponsorship?", "2026-11-01T10:00:00+00:00") == "new client"
    assert crm.record_email(s, "ana@cbre.com", "g2", "Follow up", "2026-11-03T10:00:00+00:00") == "logged"
    assert crm.record_email(s, "ana@cbre.com", "g2", "Follow up", "2026-11-03T10:00:00+00:00") == "skipped"
    db = s.all()
    assert len(db["clients"]) == 1 and db["clients"][0]["email"] == "ana@cbre.com"
    assert db["clients"][0]["company"] == "Cbre"
    assert [d["stage"] for d in db["deals"]] == [STAGES[0]]
    assert len(db["emails"]) == 2


def test_team_members_get_no_deal_and_types_are_suggested(tmp_path, monkeypatch):
    monkeypatch.setenv("TEAM_DOMAINS", "seattleunlocked.team")
    monkeypatch.setenv("LARGE_CLIENT_DOMAINS", "cbre.com")
    assert suggest_type("x@seattleunlocked.team") == "Team member"
    assert suggest_type("x@cbre.com") == "Large business"
    assert suggest_type("x@gmail.com") == "Small business"
    assert suggest_type("x@unknownco.com") == UNSORTED
    s = make_store(tmp_path)
    crm.record_email(s, "Taylor <t@seattleunlocked.team>", "g9", "Content plan", None)
    assert s.all()["deals"] == []


def test_stage_and_type_updates(tmp_path):
    s = make_store(tmp_path)
    c = crm.add_client(s, "Riley", "riley@fremont.co", UNSORTED, "Feed post")
    deal = s.all()["deals"][0]
    crm.set_stage(s, deal["id"], STAGES[2])
    crm.set_type(s, c["id"], "Small business")
    db = s.all()
    assert db["deals"][0]["stage"] == STAGES[2] and db["clients"][0]["client_type"] == "Small business"


def test_public_cards_never_show_names_or_deal_titles(tmp_path):
    s = make_store(tmp_path)
    crm.add_client(s, "Secret Person", "secret@bigco.com", "Large business", "Secret deal")
    row = build_rows(s.all())[0]
    public, private = card(row, team=False), card(row, team=True)
    assert "Secret" not in public and "bigco" not in public and "C-" in public
    assert "Secret Person" in private and "Secret deal" in private
    assert masked(row["client"]) == masked(row["client"])  # stable label


class _Fake:
    """A stand-in for the Gmail API with two emails from one sender plus one from you."""
    MSGS = {
        "m1": ("Jo Lee <jo@summitarena.com>", "Sponsorship", "Mon, 02 Nov 2026 10:00:00 +0000"),
        "m2": ("jo@summitarena.com", "Re: Sponsorship", "Tue, 03 Nov 2026 10:00:00 +0000"),
        "m3": ("Me <me@seattleunlocked.com>", "Re: Sponsorship", "Tue, 03 Nov 2026 11:00:00 +0000"),
    }

    def users(self): return self
    def messages(self): return self

    def list(self, **kw):
        self._r = {"messages": [{"id": k} for k in self.MSGS]}
        return self

    def get(self, userId, id, **kw):
        f, s, d = self.MSGS[id]
        self._r = {"snippet": "hi", "payload": {"headers": [{"name": "From", "value": f},
                   {"name": "Subject", "value": s}, {"name": "Date", "value": d}]}}
        return self

    def execute(self): return self._r


def test_gmail_sync_with_a_fake_inbox(tmp_path, monkeypatch):
    from crm.gmail_sync import sync
    monkeypatch.setenv("GMAIL_SELF", "me@seattleunlocked.com")
    s = make_store(tmp_path)
    assert sync(store=s, service=_Fake(), query="x") == {"new client": 1, "logged": 1, "skipped": 1}
    assert sync(store=s, service=_Fake(), query="x")["skipped"] == 3  # nothing logged twice
