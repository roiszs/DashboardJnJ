# create_tables.py
from database import engine, Base
import models  # importa tu modelo actualizado
from env import SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES, SQLALCHEMY_DATABASE_URL

# Esto borra la BD en memoria y crea TODO de nuevo:
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
print("🗄️  Base recreada con columna fecha.")
