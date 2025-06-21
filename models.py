# models.py
from sqlalchemy import Column, Integer, String, Float, Date
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