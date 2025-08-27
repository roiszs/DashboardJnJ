# schemas.py

from env import SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES, SQLALCHEMY_DATABASE_URL
from pydantic import BaseModel, ConfigDict, field_validator
import re

class Eficiencia(BaseModel):
    id: int
    nombre_asociado: str
    linea: str
    supervisor: str
    tipo_proceso: str
    proceso: str
    eficiencia_asociado: float
    semana: int
    turno: str
    piezas: int  
    tiempo_muerto: float = 0.0

    model_config = ConfigDict(from_attributes=True)

class EficienciaCreate(BaseModel):
    nombre_asociado: str
    linea: str
    supervisor: str
    tipo_proceso: str
    proceso: str
    eficiencia_asociado: float
    semana: int           # en lugar de fecha
    turno: str
    piezas: int 
    tiempo_muerto: float = 0.0

    model_config = ConfigDict(from_attributes=True)

    @field_validator("tipo_proceso")
    def validar_tipo_proceso(cls, v):
        if v not in ("SW", "WD"):
            raise ValueError("tipo_proceso debe ser 'SW' o 'WD'")
        return v

    @field_validator("linea", "proceso", "turno")
    def alfanumerico(cls, v):
        # Permite acentos y espacios
        if not re.fullmatch(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9 ]+", v):
            raise ValueError("Solo se permiten letras, números y espacios")
        return v
