"""Health check endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

from app.api.deps import require_admin_user
from app.core import settings

router = APIRouter()


@router.get("/healthz")
async def health_check() -> dict[str, str]:
    """Return health status."""
    return {"status": "ok"}


@router.post("/init-db")
async def init_database(
    _: dict = Depends(require_admin_user),
) -> dict[str, object]:
    """
    Initialize database schema and tables.

    Safety:
    - Requires admin user when AUTH_ENABLED=true
    - Requires ALLOW_SCHEMA_INIT=true
    """
    from app.db.session import engine
    from app.db.models import Base

    if not settings.allow_schema_init:
        raise HTTPException(
            status_code=403,
            detail="Schema init disabled. Set ALLOW_SCHEMA_INIT=true to enable.",
        )

    try:
        # Create schema if not exists (PostgreSQL only)
        if engine.dialect.name != "sqlite":
            with engine.connect() as conn:
                conn.execute(text("CREATE SCHEMA IF NOT EXISTS phase2"))
                conn.commit()

        # Create all tables (checkfirst=True skips existing tables)
        Base.metadata.create_all(bind=engine, checkfirst=True)

        # List created tables
        tables: list[str] = []
        if engine.dialect.name == "sqlite":
            with engine.connect() as conn:
                result = conn.execute(
                    text(
                        "SELECT name FROM phase2.sqlite_master "
                        "WHERE type = 'table' ORDER BY name"
                    )
                )
                tables = [row[0] for row in result]
        else:
            with engine.connect() as conn:
                result = conn.execute(
                    text(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema = 'phase2' ORDER BY table_name"
                    )
                )
                tables = [row[0] for row in result]

        return {
            "status": "ok",
            "message": f"Database initialized with {len(tables)} tables",
            "tables": tables,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize database: {str(e)}")
