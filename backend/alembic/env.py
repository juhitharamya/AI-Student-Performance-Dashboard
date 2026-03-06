from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import create_engine, pool

# Ensure `backend/` is on sys.path so `import app.*` works when running Alembic.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _get_database_url() -> str:
    from app.core.config import settings

    return os.getenv("DATABASE_URL") or settings.database_url


# Import models so Base.metadata is fully populated
from app.core.database import Base  # noqa: E402
from app.models import user, uploaded_file, student_mark  # noqa: F401, E402

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = _get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # Avoid configparser interpolation issues (e.g. `%40` in URL-encoded passwords)
    # by creating the engine directly from the URL.
    url = _get_database_url()
    connectable = create_engine(url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
