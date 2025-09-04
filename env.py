# migrations/env.py   (ALEMBIC)
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os

# IMPORTA tus modelos para obtener Base.metadata
# (models.py debería hacer: from database import Base)
from models import Base

# Alembic config
config = context.config

# Logging de Alembic, si existe alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata para autogenerate
target_metadata = Base.metadata

# Si tienes la URL de BD en variables de entorno, la inyectamos a Alembic
db_url = os.getenv("SQLALCHEMY_DATABASE_URL")
if db_url:
    config.set_main_option("sqlalchemy.url", db_url)

def run_migrations_offline() -> None:
    """Ejecuta migraciones en modo 'offline'."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Ejecuta migraciones en modo 'online'."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
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


