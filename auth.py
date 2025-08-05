# auth.py

from fastapi import Depends, HTTPException, status
from fastapi_users import FastAPIUsers, schemas
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy
from database import Base, engine, SessionLocal
from sqlalchemy import Column, Integer, String, Boolean

# 0) Tu modelo SQLAlchemy (usa el Base que viene de database.py)
class UserTable(Base):
    __tablename__ = "users"
    id              = Column(Integer, primary_key=True, index=True)
    email           = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String(length=1024), nullable=False)
    is_active       = Column(Boolean, default=True, nullable=False)
    role            = Column(String, default="viewer", nullable=False)

# 1) Los schemas de FastAPI-Users
class User(schemas.BaseUser):
    role: str

class UserCreate(schemas.BaseUserCreate):
    pass

class UserUpdate(schemas.BaseUserUpdate):
    role: str | None = None

class UserDB(User, schemas.BaseUserDB):
    pass

# 2) Crea la tabla de usuarios
Base.metadata.create_all(bind=engine)

# 3) Configura la DB de usuarios
def get_user_db():
    db = SessionLocal()
    try:
        yield SQLAlchemyUserDatabase(UserDB, db, UserTable)
    finally:
        db.close()

# 4) Transporte Bearer para el token
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

# 5) Estrategia JWT
SECRET = "TU_SECRETO_MUY_SECUR0_Y_LARGO"
jwt_strategy = JWTStrategy(secret=SECRET, lifetime_seconds=3600)

# 6) Backend de autenticación
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=lambda: jwt_strategy,
)

# 7) Instancia FastAPI-Users
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

