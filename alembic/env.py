"""Alembic environment configuration."""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool, text
from alembic import context

from app.core.config import settings
from app.db.models import Base
from app.db.session import _parse_database_url

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _escape_config_url(url: str) -> str:
    """Escape % for configparser interpolation."""
    return url.replace("%", "%%")


# Use DIRECT_URL for migrations (bypasses pgbouncer)
raw_url = settings.direct_url or settings.database_url
clean_url, _ = _parse_database_url(raw_url)
config.set_main_option("sqlalchemy.url", _escape_config_url(clean_url))


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema="phase2",
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # Create phase2 schema if not exists
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS phase2"))
        connection.commit()

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema="phase2",
            include_schemas=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
