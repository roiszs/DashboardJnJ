# models.py
from sqlalchemy import Column, Integer, String, Boolean, Float, Date, text
from database import Base
from datetime import date

class Eficiencia(Base):
    __tablename__ = "eficiencias"

    id                  = Column(Integer, primary_key=True, index=True)
    nombre_asociado     = Column(String,  nullable=False, index=True)
    linea               = Column(String,  nullable=False, index=True)
    supervisor          = Column(String,  nullable=False)
    tipo_proceso        = Column(String,  nullable=False, index=True)
    proceso             = Column(String,  nullable=False, index=True)
    eficiencia_asociado = Column(Float,   nullable=False)
    semana              = Column(Integer, nullable=False, index=True)
    fecha               = Column(Date,    nullable=False, default=date.today, index=True)
    turno               = Column(String,  nullable=False, index=True)
    piezas              = Column(Integer, nullable=False, default=1)
    tiempo_muerto       = Column(Float,   nullable=False, default=0.0, server_default=text("0.0"), index=True)

class User(Base):
    __tablename__ = "users"
    id              = Column(Integer, primary_key=True, index=True)
    email           = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active       = Column(Boolean, default=True)
    role            = Column(String, default="viewer")  # "admin" o "viewer"