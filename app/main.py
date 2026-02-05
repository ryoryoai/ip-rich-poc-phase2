"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core import get_logger, settings
from app.db.session import engine
from app.db.models import Base

logger = get_logger(__name__)


def init_database():
    """Initialize database schema and tables."""
    try:
        if not settings.allow_schema_init:
            logger.warning(
                "Schema init skipped. Set ALLOW_SCHEMA_INIT=true to enable table creation."
            )
            return

        # Create schema if not exists (PostgreSQL only)
        if engine.dialect.name != "sqlite":
            with engine.connect() as conn:
                conn.execute(text("CREATE SCHEMA IF NOT EXISTS phase2"))
                conn.commit()

        # Create all tables (checkfirst=True skips existing tables)
        Base.metadata.create_all(bind=engine, checkfirst=True)
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    logger.info("Starting Phase2 Patent Storage API")
    # Initialize database tables on startup
    init_database()
    yield
    logger.info("Shutting down Phase2 Patent Storage API")


app = FastAPI(
    title="Phase2 Patent Storage API",
    description="Japanese patent claim data storage and retrieval system",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(api_router)
