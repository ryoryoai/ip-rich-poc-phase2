"""Database session configuration."""

from contextlib import contextmanager
from typing import Generator
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from sqlalchemy import create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings


def _parse_database_url(url: str) -> tuple[str, str | None]:
    """
    Parse DATABASE_URL and extract schema parameter, keeping only standard params.

    Supabase URLs contain custom parameters like `schema`, `pgbouncer`, and
    `connection_limit` that psycopg2 doesn't recognize. This function uses a
    whitelist approach to keep only standard PostgreSQL connection parameters.

    Supports two schema specification formats:
    1. ?schema=phase2 (Supabase/Prisma style - custom parameter)
    2. ?options=-csearch_path=phase2 (libpq standard style)

    Returns:
        tuple of (clean_url with only standard params, schema name or None)
    """
    import re
    parsed = urlparse(url)

    # SQLite URLs should be returned as-is
    if parsed.scheme.startswith("sqlite"):
        # Use phase2 schema alias for SQLite tests
        return url, "phase2"

    # Parse query parameters
    query_params = parse_qs(parsed.query)

    # Extract schema for later use with SET search_path
    # Method 1: ?schema=xxx (Supabase/Prisma custom parameter)
    schema = query_params.pop("schema", [None])[0]

    # Method 2: Check if search_path is already in options parameter
    # Format: options=-csearch_path=phase2 or options=-c search_path=phase2
    options = query_params.get("options", [None])[0]
    if options and not schema:
        # Extract search_path from options
        match = re.search(r'search_path[=\s]+(\w+)', options)
        if match:
            schema = match.group(1)

    # Standard PostgreSQL/libpq connection parameters (whitelist)
    # https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-PARAMKEYWORDS
    standard_params = {
        "host", "hostaddr", "port", "dbname", "user", "password", "passfile",
        "connect_timeout", "client_encoding", "options", "application_name",
        "fallback_application_name", "keepalives", "keepalives_idle",
        "keepalives_interval", "keepalives_count", "tcp_user_timeout",
        "sslmode", "sslcompression", "sslcert", "sslkey", "sslrootcert",
        "sslcrl", "requirepeer", "krbsrvname", "gsslib", "service",
        "target_session_attrs",
    }

    # Keep only standard parameters
    filtered_params = {
        k: v for k, v in query_params.items()
        if k.lower() in standard_params
    }

    # Rebuild URL with only standard PostgreSQL parameters
    new_query = urlencode(filtered_params, doseq=True)
    clean_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment,
    ))

    return clean_url, schema


# Parse URL and extract schema
clean_database_url, db_schema = _parse_database_url(settings.database_url)

# Create engine with clean URL (no schema parameter)
engine = create_engine(
    clean_database_url,
    pool_pre_ping=True,
    echo=settings.log_level == "DEBUG",
)


# Set search_path on each connection for this specific engine
engine_url = make_url(clean_database_url)

if engine_url.get_backend_name() == "sqlite" and db_schema:
    @event.listens_for(engine, "connect")
    def attach_sqlite_schema(dbapi_connection, connection_record):
        """Attach SQLite database as schema alias for phase2."""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA database_list")
        existing = {row[1] for row in cursor.fetchall()}
        if db_schema not in existing:
            db_path = engine_url.database or ":memory:"
            cursor.execute(f"ATTACH DATABASE ? AS {db_schema}", (db_path,))
        cursor.close()

elif db_schema:
    @event.listens_for(engine, "connect")
    def set_search_path(dbapi_connection, connection_record):
        """Set PostgreSQL search_path after connection is established."""
        cursor = dbapi_connection.cursor()
        cursor.execute(f"SET search_path TO {db_schema}, public")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Context manager for database sessions."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
