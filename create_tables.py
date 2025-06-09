# create_tables.py
from database import engine, Base
import models  # esto importa todas las clases que heredan de Base

# Crea el archivo eficiencias.db y las tablas según tu modelo
Base.metadata.create_all(bind=engine)
print("Tablas creadas correctamente.")
