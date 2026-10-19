import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import create_engine, pool
from alembic import context
from dotenv import load_dotenv

# ---- Project root on sys.path ----
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# ---- Load .env ----
load_dotenv(ROOT / ".env")

# ---- Alembic Config ----
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---- Inject DATABASE_URL ----
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./comments.db")
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# ---- Model metadata ----
from app.database import Base      # noqa: E402
from app import models              # noqa: E402, F401

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # Use create_engine directly with the runtime URL — bypasses alembic.ini
    connectable = create_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()