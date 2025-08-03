from fastapi import Depends
from fastapi_users import FastAPIUsers, models as fa_models
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users.authentication import JWTAuthentication
from passlib.context import CryptContext
from database import engine, Base, SessionLocal
from models import User

# 2A) Crea el UserDBModel para FastAPI-Users
class UserModel(fa_models.BaseUser):
    role: str

class UserCreate(fa_models.BaseUserCreate):
    pass

class UserUpdate(fa_models.BaseUserUpdate):
    pass

class UserDB(UserModel, fa_models.BaseUserDB):
    pass

# 2B) Contexto de hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 2C) Base de datos de usuarios
Base.metadata.create_all(bind=engine)
user_db = SQLAlchemyUserDatabase(UserDB, SessionLocal(), User)

# 2D) Token JWT
SECRET = "TU_LLAVE_SECRETA_ALEATORIA"
auth_backends = [
    JWTAuthentication(secret=SECRET, lifetime_seconds=3600, tokenUrl="auth/jwt/login")
]

# 2E) Instancia FastAPI-Users
fastapi_users = FastAPIUsers[UserModel, UserCreate, UserUpdate, UserDB](
    user_db,
    auth_backends,
    UserModel,
    UserCreate,
    UserUpdate,
    UserDB,
)

# 2F) Rutas de auth
def get_current_active_user(user: UserDB = Depends(fastapi_users.current_user(active=True))):
    return user

def get_current_active_admin(user: UserDB = Depends(get_current_active_user)):
    if user.role != "admin":
        raise HTTPException (403, "Sólo admin") # type: ignore
    return user
