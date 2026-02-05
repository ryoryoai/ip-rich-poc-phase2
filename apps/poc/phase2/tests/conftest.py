"""Pytest configuration and fixtures."""

import os
from pathlib import Path

# Reset local test DB to avoid schema drift across runs
db_path = Path(__file__).resolve().parents[1] / "test.db"
if db_path.exists():
    db_path.unlink()

# Set test environment (force override)
os.environ["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
os.environ["DIRECT_URL"] = f"sqlite:///{db_path.as_posix()}"
os.environ["LOG_LEVEL"] = "DEBUG"
os.environ["ALLOW_SCHEMA_INIT"] = "true"
os.environ["JP_INDEX_RATE_LIMIT_PER_MINUTE"] = "0"
os.environ["JP_INDEX_CACHE_TTL_SECONDS"] = "0"
os.environ["JP_INDEX_CACHE_MAX_ENTRIES"] = "0"

# Initialize SQLite schema for tests
from app.main import init_database  # noqa: E402

init_database()
