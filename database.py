# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker as async_sessionmaker

import env as app_env 

# ---------- Declarative Base (SQLAlchemy 2.0) ----------
class Base(DeclarativeBase):
    pass

# =======================================================
#        CONEXIÓN SÍNCRONA (tu app / CRUD actual)
# =======================================================
SQLALCHEMY_DATABASE_URL = "sqlite:///./eficiencias.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # requerido por SQLite
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# =======================================================
#        CONEXIÓN ASÍNCRONA (fastapi-users)
# =======================================================
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker as async_sessionmaker

ASYNC_SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./eficiencias.db"

async_engine = create_async_engine(
    ASYNC_SQLALCHEMY_DATABASE_URL,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Carga URLs desde env.py con valores por defecto
SYNC_DB_URL  = getattr(app_env, "SQLALCHEMY_DATABASE_URL", "sqlite:///./eficiencias.db")
ASYNC_DB_URL = getattr(app_env, "ASYNC_SQLALCHEMY_DATABASE_URL", "") or (
    "sqlite+aiosqlite://" + SYNC_DB_URL[len("sqlite://"):]
    if SYNC_DB_URL.startswith("sqlite:///") else SYNC_DB_URL
)

