"""Health check endpoint."""

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

router = APIRouter()


@router.get("/healthz")
async def health_check() -> dict[str, str]:
    """Return health status."""
    return {"status": "ok"}


@router.post("/init-db")
async def init_database() -> dict[str, str]:
    """Initialize database schema and tables."""
    from app.db.session import engine
    from app.db.models import Base

    try:
        # Create schema if not exists
        with engine.connect() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS phase2"))
            conn.commit()

        # Create all tables (checkfirst=True skips existing tables)
        Base.metadata.create_all(bind=engine, checkfirst=True)

        # List created tables
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'phase2' ORDER BY table_name"
            ))
            tables = [row[0] for row in result]

        return {
            "status": "ok",
            "message": f"Database initialized with {len(tables)} tables",
            "tables": tables,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize database: {str(e)}")
