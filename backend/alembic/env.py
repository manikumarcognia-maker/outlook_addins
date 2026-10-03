from logging.config import fileConfig

import psycopg
from sqlalchemy import create_engine, pool

from alembic import context
from rag.config import settings
from rag.pg_conn import build_database_conninfo, connection_kwargs

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None


def _sqlalchemy_url() -> str:
    url = settings.DATABASE_URL
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    return url


def _create_engine():
    conninfo = build_database_conninfo(settings.DATABASE_URL)
    return create_engine(
        "postgresql+psycopg://",
        creator=lambda: psycopg.connect(conninfo, **connection_kwargs()),
        poolclass=pool.NullPool,
    )


def run_migrations_offline() -> None:
    context.configure(
        url=_sqlalchemy_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = _create_engine()

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
