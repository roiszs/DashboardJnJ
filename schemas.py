from pydantic import BaseModel, ConfigDict, field_validator, EmailStr
import re


# =========================
# ESQUEMAS DE EFICIENCIA
# =========================
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
    semana: int
    turno: str
    piezas: int 
    tiempo_muerto: float = 0.0

    model_config = ConfigDict(from_attributes=True)

    # ---------- Validaciones ----------
    @field_validator("tipo_proceso")
    def validar_tipo_proceso(cls, v):
        if v not in ("SW", "WD"):
            raise ValueError("tipo_proceso debe ser 'SW' o 'WD'")
        return v

    @field_validator("linea", "proceso", "turno")
    def alfanumerico(cls, v):
        if not re.fullmatch(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9 ]+", v):
            raise ValueError("Solo se permiten letras, números y espacios")
        return v

    @field_validator("eficiencia_asociado")
    def validar_eficiencia(cls, v):
        if not (0 <= v <= 100):
            raise ValueError("eficiencia_asociado debe estar entre 0 y 100")
        return v

    @field_validator("piezas")
    def validar_piezas(cls, v):
        if v < 0:
            raise ValueError("piezas debe ser un número positivo")
        return v


# =========================
# ESQUEMAS DE USUARIO
# =========================
class UserRead(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    is_superuser: bool
    is_verified: bool
    role: str   # <- campo adicional definido en tu modelo

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "viewer"   # por defecto los usuarios son "viewer"

    model_config = ConfigDict(from_attributes=True)

    @field_validator("role")
    def validar_role(cls, v):
        if v not in ("admin", "viewer"):
            raise ValueError("El rol debe ser 'admin' o 'viewer'")
        return v


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    password: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None
    is_verified: bool | None = None
    role: str | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("role")
    def validar_role(cls, v):
        if v and v not in ("admin", "viewer"):
            raise ValueError("El rol debe ser 'admin' o 'viewer'")
        return v
