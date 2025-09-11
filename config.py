# config.py
import os
from dotenv import load_dotenv

# Cargar variables desde .env si existe
load_dotenv()

# Variables de configuración
SECRET_KEY = os.getenv("SECRET_KEY", "super_secreto")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 2880))

SQLALCHEMY_DATABASE_URL = os.getenv(
    "SQLALCHEMY_DATABASE_URL",
    "sqlite:///./eficiencias.db"
)

ASYNC_SQLALCHEMY_DATABASE_URL = os.getenv(
    "ASYNC_SQLALCHEMY_DATABASE_URL",
    "sqlite+aiosqlite:///./eficiencias.db"
)
