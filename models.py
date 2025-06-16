# models.py
from sqlalchemy import Column, Integer, String, Float, Date, text
from database import Base

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
    fecha               = Column(Date,    nullable=False, server_default=text("CURRENT_DATE"), index=True)
    turno               = Column(String,  nullable=False, index=True)
