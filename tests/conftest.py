"""Pytest configuration and fixtures.

Uses testcontainers to spin up a PostgreSQL container per test session,
eliminating SQLite/PostgreSQL incompatibilities (UUID, TSVECTOR, schema).
Requires Docker Desktop to be running.
"""

import os

from testcontainers.postgres import PostgresContainer

# Start PostgreSQL container BEFORE any app module imports,
# because app.db.session reads DATABASE_URL at module level.
_pg = PostgresContainer(
    image="postgres:16-alpine",
    port=5432,
    dbname="testdb",
    username="testuser",
    password="testpass",
)
_pg.start()

_host = _pg.get_container_host_ip()
_port = _pg.get_exposed_port(5432)
_db_url = (
    f"postgresql://testuser:testpass@{_host}:{_port}"
    f"/testdb?options=-csearch_path=phase2,public"
)

# Set environment BEFORE importing any app modules
os.environ["DATABASE_URL"] = _db_url
os.environ["DIRECT_URL"] = _db_url
os.environ["LOG_LEVEL"] = "DEBUG"
os.environ["ALLOW_SCHEMA_INIT"] = "true"
os.environ["JP_INDEX_RATE_LIMIT_PER_MINUTE"] = "0"
os.environ["JP_INDEX_CACHE_TTL_SECONDS"] = "0"
os.environ["JP_INDEX_CACHE_MAX_ENTRIES"] = "0"
os.environ["AUTH_ENABLED"] = "false"

# NOW import and initialize
from app.main import init_database  # noqa: E402

init_database()

# Insert default tenant (required for FK constraints on tenant_id columns)
import uuid as _uuid  # noqa: E402

from app.db.models import Tenant  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402

_session = SessionLocal()
_existing = _session.get(Tenant, _uuid.UUID("a0000000-0000-0000-0000-000000000001"))
if not _existing:
    _session.add(Tenant(
        id=_uuid.UUID("a0000000-0000-0000-0000-000000000001"),
        name="default",
        slug="default",
    ))
    _session.commit()
_session.close()


def pytest_sessionfinish(session, exitstatus):
    """Stop the PostgreSQL container when the test session ends."""
    _pg.stop()
