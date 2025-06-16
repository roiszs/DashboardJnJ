# create_tables.py
from database import engine, Base
import models  # importa tu modelo actualizado

# Esto borra la BD en memoria y crea TODO de nuevo:
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
print("🗄️  Base recreada con columna fecha.")
