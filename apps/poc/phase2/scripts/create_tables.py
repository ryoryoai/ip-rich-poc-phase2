"""Script to create all tables in the phase2 schema."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.db.session import engine
from app.db.models import Base


def create_tables():
    """Create all tables defined in models."""
    # First, create the schema if it doesn't exist
    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS phase2"))
        conn.commit()
        print("Schema 'phase2' created or already exists")

    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("All tables created successfully!")

    # List created tables
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'phase2' ORDER BY table_name"
        ))
        tables = [row[0] for row in result]
        print(f"\nTables in phase2 schema ({len(tables)}):")
        for table in tables:
            print(f"  - {table}")


if __name__ == "__main__":
    create_tables()
