import asyncio
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import Connection, pool
from sqlalchemy.ext.asyncio import create_async_engine

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from src.domain.common.models import Base  # noqa: E402
from src.low.config.reader import ConfigReader  # noqa: E402
from src.low.creds.reader import CredsReader  # noqa: E402
from src.low.database.database import Database  # noqa: E402

target_metadata = Base.metadata


def _build_url() -> str:
    """Читает URL из файлов конфигурации проекта."""
    config_dir = Path("config/prod")
    cfg = ConfigReader.load(config_dir / "config.json")
    creds = CredsReader.load(config_dir / cfg.general.creds)
    return Database(cfg.modules.database, creds.modules.database)._build_database_url()


def run_migrations_offline() -> None:
    context.configure(
        url=_build_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    engine = create_async_engine(_build_url(), poolclass=pool.NullPool)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
