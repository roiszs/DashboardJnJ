# models.py
from datetime import date
from sqlalchemy import String, Float, Date, Integer, text
from sqlalchemy.orm import Mapped, mapped_column
from database import Base
from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTable


# =========================
# Usuarios
# =========================
class User(SQLAlchemyBaseUserTable[int], Base):
    __tablename__ = "users"

    # PK explícita (FastAPI-Users requiere definirla)
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True
    )

    # Campo adicional: rol
    role: Mapped[str] = mapped_column(String, default="viewer", nullable=False)


# =========================
# Eficiencias
# =========================
class Eficiencia(Base):
    __tablename__ = "eficiencias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre_asociado: Mapped[str] = mapped_column(String, nullable=False, index=True)
    linea: Mapped[str] = mapped_column(String, nullable=False, index=True)
    supervisor: Mapped[str] = mapped_column(String, nullable=False)
    tipo_proceso: Mapped[str] = mapped_column(String, nullable=False, index=True)
    proceso: Mapped[str] = mapped_column(String, nullable=False, index=True)
    eficiencia_asociado: Mapped[float] = mapped_column(Float, nullable=False)

    semana: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    fecha: Mapped[date] = mapped_column(Date, nullable=False, default=date.today, index=True)
    turno: Mapped[str] = mapped_column(String, nullable=False, index=True)

    piezas: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # minutos de downtime, con default en 0
    tiempo_muerto: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        server_default=text("0.0"),
        index=True,
    )
