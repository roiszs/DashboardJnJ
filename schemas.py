# schemas.py (añade junto al modelo de lectura)
from pydantic import BaseModel
from datetime import date
from typing import Optional

class EficienciaCreate(BaseModel):
    nombre_asociado: str
    wwid: int
    linea: str
    supervisor: str
    proceso: str            # "SW" o "WD"
    numero_batch: str
    eficiencia_asociado: float
    eficiencia_linea: Optional[float] = None
    fecha: date
    turno: str
