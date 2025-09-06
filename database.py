# database.py
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker as async_sessionmaker

import config as app_env



# ============= Declarative Base (SQLAlchemy 2.0) =============
class Base(DeclarativeBase):
    pass


# ============= URLs de BD (cargadas desde env.py) =============
# URL síncrona (principal de la app)
SYNC_DB_URL = getattr(app_env, "SQLALCHEMY_DATABASE_URL", "sqlite:///./eficiencias.db")

# URL asíncrona (opcional). Si no la defines en env.py y usas SQLite,
# la derivamos automáticamente a aiosqlite.
ASYNC_DB_URL = getattr(app_env, "ASYNC_SQLALCHEMY_DATABASE_URL", "") or (
    # Derivar sólo si la sync es sqlite:///
    ("sqlite+aiosqlite://" + SYNC_DB_URL[len("sqlite://"):])
    if SYNC_DB_URL.startswith("sqlite:///")
    else ""
)

# (Opcional) exportar con los mismos nombres que algunos módulos esperan
SQLALCHEMY_DATABASE_URL = SYNC_DB_URL
ASYNC_SQLALCHEMY_DATABASE_URL = ASYNC_DB_URL


# ============= Motor y sesión SÍNCRONOS =============
# Para SQLite se requiere check_same_thread=False
sync_connect_args = {"check_same_thread": False} if SYNC_DB_URL.startswith("sqlite") else {}

engine = create_engine(
    SYNC_DB_URL,
    connect_args=sync_connect_args,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


# ============= Motor y sesión ASÍNCRONOS =============
# Si no tienes uso asíncrono, igual lo dejamos disponible (no molesta).
if not ASYNC_DB_URL:
    # Si no hay URL async y tampoco era SQLite, puedes comentar esto
    # o levantar excepción si realmente necesitas async.
    # Para simplificar, si no se puede derivar, no creamos motor async.
    async_engine = None
    AsyncSessionLocal = None
else:
    async_engine = create_async_engine(
        ASYNC_DB_URL,
        future=True,
    )
    AsyncSessionLocal = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


# ============= Dependencias para FastAPI =============
def get_db():
    """Dependencia síncrona: inyecta una sesión de BD por request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db():
    """Dependencia asíncrona: inyecta una sesión async por request (si existe)."""
    if AsyncSessionLocal is None:
        raise RuntimeError("No hay motor de base de datos asíncrono configurado.")
    async with AsyncSessionLocal() as session:
        yield session
