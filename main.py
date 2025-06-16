from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from collections import defaultdict
import models, schemas
from database import SessionLocal, engine

# 1) Crea las tablas
models.Base.metadata.create_all(bind=engine)


app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 3) Endpoints de tu API

@app.get("/api/eficiencias", response_model=list[schemas.Eficiencia])
def leer_eficiencias(db: Session = Depends(get_db)):
    # Trae los 100 registros con mayor id (los más recientes),
    # luego invierte el orden para mostrarlos cronológicamente
    recientes = (
        db.query(models.Eficiencia)
          .order_by(models.Eficiencia.id.desc())
          .limit(100)
          .all()
    )
    return list(reversed(recientes))


@app.post("/api/eficiencias", response_model=schemas.Eficiencia, status_code=201)
def crear_eficiencia(payload: schemas.EficienciaCreate, db: Session = Depends(get_db)):
    registro = models.Eficiencia(**payload.dict())
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return registro

@app.delete("/api/eficiencias/{ef_id}", status_code=status.HTTP_204_NO_CONTENT)
def borrar_eficiencia(ef_id: int, db: Session = Depends(get_db)):
    reg = db.query(models.Eficiencia).filter(models.Eficiencia.id == ef_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    db.delete(reg)
    db.commit()


# 4) Monta los estáticos en /static
app.mount("/static", StaticFiles(directory="static"), name="static")

# 5) Sirve tus páginas HTML
@app.get("/", response_class=FileResponse)
def serve_dashboard():
    return "static/index.html"

@app.get("/add.html", response_class=FileResponse)
def serve_form():
    return "static/add.html"

from collections import defaultdict

@app.get("/api/eficiencias/weekly")
def eficiencia_semanal_iso(db: Session = Depends(get_db)):
    # 1) Trae todos los registros
    items = db.query(models.Eficiencia).all()

    # 2) Agrupa por (año, semana ISO, proceso) y acumula eficiencias de asociados
    grupos = defaultdict(list)
    for r in items:
        year, week, _ = r.fecha.isocalendar()  # ISO-week
        grupos[(year, week, r.proceso)].append(r.eficiencia_asociado)

    # 3) Construye la salida con promedio
    salida = []
    for (year, week, proceso), vals in grupos.items():
        salida.append({
            "semana": f"{year}-{week:02d}",           # ej. "2025-04"
            "proceso": proceso,
            "promedio_asociado": round(sum(vals)/len(vals), 2)
        })

    # 4) Ordénalo y devuelve
    salida.sort(key=lambda x: x["semana"])
    return salida

from sqlalchemy import func
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
import models
from database import SessionLocal

# Eficiencia diaria por proceso
@app.get("/api/eficiencias/daily/process")
def eficiencia_diaria_proceso(db: Session = Depends(get_db)):
    q = (
        db.query(
            models.Eficiencia.fecha.label("fecha"),
            models.Eficiencia.proceso,
            func.avg(models.Eficiencia.eficiencia_asociado).label("promedio_asociado")
        )
        .group_by(models.Eficiencia.fecha, models.Eficiencia.proceso)
        .order_by(models.Eficiencia.fecha)
    )
    return [
        {"fecha": f.isoformat(), "proceso": p, "promedio_asociado": float(avg)}
        for f, p, avg in q.all()
    ]

# Eficiencia diaria por línea
@app.get("/api/eficiencias/daily/line")
def eficiencia_diaria_linea(db: Session = Depends(get_db)):
    q = (
        db.query(
            models.Eficiencia.fecha.label("fecha"),
            models.Eficiencia.linea,
            func.avg(models.Eficiencia.eficiencia_asociado).label("promedio_asociado")
        )
        .group_by(models.Eficiencia.fecha, models.Eficiencia.linea)
        .order_by(models.Eficiencia.fecha)
    )
    return [
        {"fecha": f.isoformat(), "linea": l, "promedio_asociado": float(avg)}
        for f, l, avg in q.all()
    ]

from sqlalchemy import func

#Top Asociados
@app.get("/api/eficiencias/top-associates")
def top_associados(limit: int = 5, db: Session = Depends(get_db)):
    """
    Devuelve los top `limit` asociados ordenados por eficiencia_asociado promedio descendente.
    """
    q = (
        db.query(
            models.Eficiencia.nombre_asociado.label("nombre"),
            func.avg(models.Eficiencia.eficiencia_asociado).label("promedio_asociado")
        )
        .group_by(models.Eficiencia.nombre_asociado)
        .order_by(func.avg(models.Eficiencia.eficiencia_asociado).desc())
        .limit(limit)
    )
    return [
        {"nombre": nombre, "promedio_asociado": float(round(prom, 2))}
        for nombre, prom in q.all()
    ]

from sqlalchemy import func

#Eficiencia por turno
@app.get("/api/eficiencias/shift")
def eficiencia_por_turno(db: Session = Depends(get_db)):
    """
    Devuelve el promedio de eficiencia_asociado para cada turno.
    """
    q = (
        db.query(
            models.Eficiencia.turno.label("turno"),
            func.avg(models.Eficiencia.eficiencia_asociado).label("promedio_asociado")
        )
        .group_by(models.Eficiencia.turno)
        .order_by(models.Eficiencia.turno)
    )
    return [
        {"turno": turno, "promedio_asociado": float(round(prom, 2))}
        for turno, prom in q.all()
    ]

from sqlalchemy import func

#Eficiencia por SW & WD
@app.get("/api/eficiencias/counts")
def conteo_sw_wd_por_linea(db: Session = Depends(get_db)):
    """
    Devuelve, para cada línea, cuántos registros de tipo_proceso SW y WD hay.
    """
    q = (
        db.query(
            models.Eficiencia.linea.label("linea"),
            models.Eficiencia.tipo_proceso.label("tipo_proceso"),
            func.count().label("count")
        )
        .group_by(models.Eficiencia.linea, models.Eficiencia.tipo_proceso)
        .order_by(models.Eficiencia.linea)
    )
    return [
        {"linea": linea, "tipo_proceso": tp, "count": cnt}
        for linea, tp, cnt in q.all()
    ]
