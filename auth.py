# auth.py

from fastapi import Depends, HTTPException, status
from fastapi_users import FastAPIUsers
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users.models import BaseUser, BaseUserCreate, BaseUserUpdate, BaseUserDB
from fastapi_users.password import get_password_hash, PasswordHelper
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from database import Base, engine, SessionLocal
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy.orm import Mapped, mapped_column

# 0) Tu modelo SQLAlchemy
Base: DeclarativeMeta = declarative_base()

class UserTable(Base):
    __tablename__ = "users"
    id              = Column(Integer, primary_key=True, index=True)
    email           = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String(length=1024), nullable=False)
    is_active       = Column(Boolean, default=True, nullable=False)
    role            = Column(String, default="viewer", nullable=False)

# 1) Los schemas de FastAPI-Users
class User(BaseUser):
    role: str

class UserCreate(BaseUserCreate):
    pass

class UserUpdate(BaseUserUpdate):
    role: str | None = None

class UserDB(User, BaseUserDB):
    pass

# 2) Creamos la tabla de usuarios
Base.metadata.create_all(bind=engine)

# 3) Configuramos la DB de usuarios
def get_user_db():
    db = SessionLocal()
    try:
        yield SQLAlchemyUserDatabase(UserDB, db, UserTable)
    finally:
        db.close()

# 4) Transport para el token (Bearer)
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

# 5) Estrategia JWT
SECRET = "TU_SECRETO_MUY_SEGUR0_Y_LARGO"
jwt_strategy = JWTStrategy(secret=SECRET, lifetime_seconds=3600)

# 6) Backend de autenticación
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=lambda: jwt_strategy,
)

# 7) Instanciamos FastAPI-Users
fastapi_users = FastAPIUsers[User, UserCreate, UserUpdate, UserDB](
    get_user_db,
    [auth_backend],
    User,
    UserCreate,
    UserUpdate,
    UserDB,
)

# 8) Dependencias para proteger rutas
get_current_active_user = fastapi_users.current_user(active=True)
def get_current_active_admin(
    user: UserDB = Depends(get_current_active_user),
):
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo admin puede acceder",
        )
    return user

