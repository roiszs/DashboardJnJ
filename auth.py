# auth.py

from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status
from fastapi_users import FastAPIUsers
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy
from fastapi_users.models import BaseUser, BaseUserCreate, BaseUserUpdate, BaseUserDB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean
from database import engine, SessionLocal

# SQLAlchemy base
Base = declarative_base()

# — 0) Modelo de tabla “users” —
class UserTable(Base):
    __tablename__ = "users"
    id              = Column(Integer, primary_key=True, index=True)
    email           = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String(length=1024), nullable=False)
    is_active       = Column(Boolean, default=True, nullable=False)
    role            = Column(String, default="viewer", nullable=False)

# Creamos la tabla si no existe
Base.metadata.create_all(bind=engine)

# — 1) Esquemas Pydantic de FastAPI-Users —
class User(BaseUser[int]):
    role: str

class UserCreate(BaseUserCreate[int]):
    role: Optional[str] = None

class UserUpdate(BaseUserUpdate[int]):
    role: Optional[str] = None

class UserDB(User, BaseUserDB[int]):
    pass

# — 2) Dependency para la DB de usuarios —
async def get_user_db() -> AsyncGenerator[SQLAlchemyUserDatabase, None]:
    db = SessionLocal()
    yield SQLAlchemyUserDatabase(UserDB, db, UserTable)
    db.close()

# — 3) Configuración del backend JWT —
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")
SECRET = "TU_SECRETO_MUY_SEGUR0_Y_LARGO"  # Cámbialo por uno seguro en producción
jwt_strategy = JWTStrategy(secret=SECRET, lifetime_seconds=3600)

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=lambda: jwt_strategy,
)

# — 4) Instancia FastAPI-Users —
fastapi_users = FastAPIUsers[User, UserCreate, UserUpdate, UserDB](
    get_user_db,
    [auth_backend],
    User,
    UserCreate,
    UserUpdate,
    UserDB,
)

# — 5) Dependencias para proteger rutas —
get_current_active_user = fastapi_users.current_user(active=True)

def get_current_active_admin(
    user: UserDB = Depends(get_current_active_user),
):
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden hacer eso",
        )
    return user

