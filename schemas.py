# schemas.py
from pydantic import BaseModel, ConfigDict, field_validator
from datetime import date
from typing import Optional
import re

class Eficiencia(BaseModel):
    id: int
    nombre_asociado: str
    linea: str
    supervisor: str
    tipo_proceso: str
    proceso: str
    eficiencia_asociado: float
    fecha: date
    turno: str

    model_config = ConfigDict(from_attributes=True)

class EficienciaCreate(BaseModel):
    nombre_asociado: str
    linea: str
    supervisor: str
    tipo_proceso: str
    proceso: str
    eficiencia_asociado: float
    fecha: date
    turno: str

    model_config = ConfigDict(from_attributes=True)

    @field_validator("tipo_proceso")
    def validar_tipo_proceso(cls, v):
        if v not in ("SW", "WD"):
            raise ValueError("tipo_proceso debe ser 'SW' o 'WD'")
        return v

    @field_validator("linea", "proceso", "turno")
    def alfanumerico(cls, v):
        if not re.fullmatch(r"[A-Za-z0-9 ]+", v):
            raise ValueError("Solo se permiten letras, números y espacios")
        return v
