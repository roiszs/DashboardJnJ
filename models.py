# models.py
from sqlalchemy import Column, Integer, String, Date, Float
from database import Base

class Eficiencia(Base):
    __tablename__ = "eficiencias"

    id                 = Column(Integer, primary_key=True, index=True)
    nombre_asociado    = Column(String, nullable=False, index=True)
    # wwid            -- ELIMINADO
    linea              = Column(String, nullable=False, index=True)
    supervisor         = Column(String, nullable=False)
    tipo_proceso       = Column(String, nullable=False, index=True)
    proceso            = Column(String, nullable=False, index=True)
    # numero_batch    -- ELIMINADO
    eficiencia_asociado = Column(Float, nullable=False)
    # eficiencia_linea -- ELIMINADO (la calcularemos en nuestros endpoints)
    fecha              = Column(Date, nullable=False, index=True)
    turno              = Column(String, nullable=False, index=True)
