import pytest


@pytest.fixture(autouse=True)
def _fresh_settings_cache(monkeypatch):
    """Each test reads team settings fresh, and never touches the real Supabase from .env."""
    import kvstore
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_KEY", raising=False)
    kvstore._cache.clear()
    yield
    kvstore._cache.clear()
