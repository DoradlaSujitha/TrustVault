from backend.database import normalize_database_url


def test_normalize_render_postgres_url():
    assert normalize_database_url("postgres://user:pass@host/db") == "postgresql+psycopg://user:pass@host/db"


def test_normalize_standard_postgresql_url():
    assert normalize_database_url("postgresql://user:pass@host/db") == "postgresql+psycopg://user:pass@host/db"


def test_leave_sqlite_url_unchanged():
    assert normalize_database_url("sqlite:///./trustvault.db") == "sqlite:///./trustvault.db"
