# models.py
from sqlalchemy import Column, Integer, String, Date, Float
from database import Base

class Eficiencia(Base):
    __tablename__ = "eficiencias"

    id                  = Column(Integer, primary_key=True, index=True)
    nombre_asociado     = Column(String,  nullable=False, index=True)
    wwid                = Column(Integer, nullable=False, index=True)
    linea               = Column(String,  nullable=False, index=True)  # p.ej. "1" o "Línea A"
    supervisor          = Column(String,  nullable=False)
    proceso             = Column(String,  nullable=False, index=True)  # "SW" o "WD"
    numero_batch        = Column(String,  nullable=False)
    eficiencia_asociado = Column(Float,   nullable=False)
    eficiencia_linea    = Column(Float,   nullable=True)  # opcional: suele calcularse agrupando
    fecha               = Column(Date,    nullable=False, index=True)
    turno               = Column(String,  nullable=False, index=True)

