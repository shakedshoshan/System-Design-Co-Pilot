from __future__ import annotations

import os
import sys
from pathlib import Path

# This file lives at apps/api/migrations/env.py — force this API tree first so `import app`
# resolves here, not another project on PYTHONPATH (e.g. a different monorepo).
_API_ROOT = str(Path(__file__).resolve().parents[1])
if _API_ROOT in sys.path:
    sys.path.remove(_API_ROOT)
sys.path.insert(0, _API_ROOT)

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import get_settings
from app.db.base import Base
from app.db import models as _models  # noqa: F401 — register metadata

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    url = (os.environ.get("DATABASE_URL") or "").strip() or get_settings().database_url
    if not url:
        raise RuntimeError(
            "DATABASE_URL must be set for Alembic (repo root `.env` or environment)."
        )
    return url


def run_migrations_offline() -> None:
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
