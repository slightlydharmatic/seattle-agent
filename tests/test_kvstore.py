"""Team settings: Supabase when connected, local files otherwise."""
import kvstore


class FakeTable:
    def __init__(self, rows): self.rows, self._q = rows, {}
    def select(self, *_): return self
    def eq(self, k, v): self._q = {k: v}; return self
    def limit(self, _): return self
    def upsert(self, row, on_conflict): self.rows[row["name"]] = row["value"]; return self
    def execute(self):
        name = self._q.get("name")
        class R: data = [{"value": self.rows[name]}] if name in self.rows else []
        return R


class FakeDB:
    def __init__(self): self.t = FakeTable({})
    def table(self, _): return self.t


def test_local_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(kvstore, "DATA", tmp_path)
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    kvstore._cache.clear()
    assert kvstore.where() == "local"
    kvstore.put("custom_events", [{"title": "Potluck"}])
    kvstore._cache.clear()
    assert kvstore.get("custom_events") == [{"title": "Potluck"}]


def test_supabase_round_trip(monkeypatch):
    db = FakeDB()
    monkeypatch.setenv("SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "test")
    monkeypatch.setattr(kvstore, "client", lambda: db)
    kvstore._cache.clear()
    assert kvstore.where() == "supabase"
    kvstore.put("filters", {"allow": ["a|2026-11-08"]})
    kvstore._cache.clear()
    assert kvstore.get("filters") == {"allow": ["a|2026-11-08"]}
    assert db.t.rows["filters"]["allow"] == ["a|2026-11-08"]
    kvstore._cache.clear()
