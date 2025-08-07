# auth.py
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi_users import FastAPIUsers
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users.models import BaseUser, BaseUserCreate, BaseUserUpdate, BaseUserDB
from fastapi_users.authentication import (
    BearerTransport,
    JWTStrategy,
    AuthenticationBackend,
)
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
from sqlalchemy import Column, Integer, String, Boolean
from database import engine, SessionLocal

# 0) Tu modelo SQLAlchemy de la tabla "users"
Base: DeclarativeMeta = declarative_base()

class UserTable(Base):
    __tablename__ = "users"
    id              = Column(Integer, primary_key=True, index=True)
    email           = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String(length=1024), nullable=False)
    is_active       = Column(Boolean, default=True, nullable=False)
    role            = Column(String, default="viewer", nullable=False)

# Crea la tabla si no existía
Base.metadata.create_all(bind=engine)

# 1) Pydantic schemas de FastAPI-Users (sin parámetros genéricos)
class User(BaseUser):
    role: str

class UserCreate(BaseUserCreate):
    role: Optional[str] = None

class UserUpdate(BaseUserUpdate):
    role: Optional[str] = None

class UserDB(User, BaseUserDB):
    pass

# 2) Dependency que proporciona el UserDB
async def get_user_db():
    db = SessionLocal()
    try:
        yield SQLAlchemyUserDatabase(UserDB, db, UserTable)
    finally:
        db.close()

# 3) Configuración de JWT
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")
SECRET = "TU_SECRETO_MUY_SEGUR0_Y_LARGO"
jwt_strategy = JWTStrategy(secret=SECRET, lifetime_seconds=3600)

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=lambda: jwt_strategy,
)

# 4) Instancia FastAPI-Users
fastapi_users = FastAPIUsers(
    get_user_db,
    [auth_backend],
    User,
    UserCreate,
    UserUpdate,
    UserDB,
)

# 5) Dependencias para proteger rutas
get_current_active_user = fastapi_users.current_user(active=True)

def get_current_active_admin(
    user: UserDB = Depends(get_current_active_user)
):
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden acceder",
        )
    return user

