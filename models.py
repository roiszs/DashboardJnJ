# models.py
from sqlalchemy import Column, Integer, String, Date, Float
from database import Base

class Eficiencia(Base):
    __tablename__ = "eficiencias"

    id    = Column(Integer, primary_key=True, index=True)
    linea = Column(String, index=True)
    fecha = Column(Date,   index=True)
    turno = Column(String, index=True)
    valor = Column(Float)
