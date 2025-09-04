# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from env import SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES, SQLALCHEMY_DATABASE_URL

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

