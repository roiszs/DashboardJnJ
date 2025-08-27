# auth.py (versión pulida)
from typing import Optional, AsyncGenerator
from collections.abc import Generator
from .env import SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES, SQLALCHEMY_DATABASE_URL

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from fastapi_users import FastAPIUsers, BaseUserManager, IntegerIDMixin, schemas
from fastapi_users.authentication import BearerTransport, JWTStrategy, AuthenticationBackend
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase

from database import SessionLocal, AsyncSessionLocal
from models import User

# ====== DB session dep ======
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

        # ====== DB async (fastapi-users) ======
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

async def get_user_db(
    session: Session = Depends(get_async_db),
) -> AsyncGenerator[SQLAlchemyUserDatabase, None]:
    yield SQLAlchemyUserDatabase(session, User)

# ====== User Schemas ======
class UserRead(schemas.BaseUser[int]):
    role: str

class UserCreate(schemas.BaseUserCreate):
    role: str = "viewer"

class UserUpdate(schemas.BaseUserUpdate):
    role: Optional[str] = None

# ====== User Manager ======
SECRET = "TU_SECRETO_MUY_SEGUR0_Y_LARGO"

class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User, request=None):
        pass

async def get_user_manager(user_db=Depends(get_user_db)) -> AsyncGenerator[UserManager, None]:
    yield UserManager(user_db)

# ====== Auth backend (JWT Bearer) ======
bearer_transport = BearerTransport(tokenUrl="/auth/jwt/login")

def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

# ====== FastAPI-Users instance ======
fastapi_users = FastAPIUsers[User, int](get_user_manager, [auth_backend])

get_current_active_user = fastapi_users.current_user(active=True)

def get_current_active_admin(user: User = Depends(get_current_active_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Solo los administradores pueden acceder")
    return user


