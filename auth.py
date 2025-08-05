# auth.py

from typing import Optional, AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi_users import FastAPIUsers
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users import schemas as fu_schemas
from fastapi_users.password import get_password_hash, PasswordHelper
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from database import Base, engine, SessionLocal
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base

# 0) Tu modelo SQLAlchemy de la tabla "users"
Base: DeclarativeMeta = declarative_base()

class UserTable(Base):
    __tablename__ = "users"
    id              = Column(Integer, primary_key=True, index=True)
    email           = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String(length=1024), nullable=False)
    is_active       = Column(Boolean, default=True, nullable=False)
    role            = Column(String, default="viewer", nullable=False)

# 1) Los Pydantic schemas de FastAPI-Users, importados desde fastapi_users.schemas
class User(fu_schemas.BaseUser[int]):
    role: str

class UserCreate(fu_schemas.BaseUserCreate):
    pass

class UserUpdate(fu_schemas.BaseUserUpdate):
    role: Optional[str] = None

class UserDB(User, fu_schemas.BaseUserDB[int]):
    pass

# 2) Crea la tabla "users" en la BD (solo la primera vez)
Base.metadata.create_all(bind=engine)

# 3) Configura el backend de usuarios de FastAPI-Users
async def get_user_db() -> AsyncGenerator[SQLAlchemyUserDatabase, None]:
    db = SessionLocal()
    try:
        yield SQLAlchemyUserDatabase(UserDB, db, UserTable)
    finally:
        db.close()

# 4) Transport y estrategia JWT
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")
SECRET = "TU_SECRETO_MUY_SEGUR0_Y_LARGO"
jwt_strategy = JWTStrategy(secret=SECRET, lifetime_seconds=3600)

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=lambda: jwt_strategy,
)

# 5) Instancia FastAPI-Users
fastapi_users = FastAPIUsers[User, UserCreate, UserUpdate, UserDB](
    get_user_db,
    [auth_backend],
    User,
    UserCreate,
    UserUpdate,
    UserDB,
)

# 6) Dependencias para proteger rutas
get_current_active_user = fastapi_users.current_user(active=True)

def get_current_active_admin(
    user: UserDB = Depends(get_current_active_user),
):
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los admins pueden acceder",
        )
    return user

