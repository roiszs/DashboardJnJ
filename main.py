from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from collections import defaultdict
import models, schemas
from database import SessionLocal, engine
from datetime import date
from typing import Optional


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
def leer_eficiencias(
    start: Optional[date] = None,
    end:   Optional[date] = None,
    linea: Optional[str]  = None,
    proceso: Optional[str]= None,
    db: Session = Depends(get_db)
):
    q = db.query(models.Eficiencia)
    if start:
        q = q.filter(models.Eficiencia.fecha >= start)
    if end:
        q = q.filter(models.Eficiencia.fecha <= end)
    if linea:
        q = q.filter(models.Eficiencia.linea == linea)
    if proceso:
        q = q.filter(models.Eficiencia.proceso == proceso)

    recientes = (
        q.order_by(models.Eficiencia.id.desc())
         .limit(100)
         .all()
    )
    return list(reversed(recientes))

#Select de filtros
@app.get("/api/eficiencias/lines")
def get_lines(db: Session = Depends(get_db)):
    rows = db.query(models.Eficiencia.linea)\
             .distinct()\
             .order_by(models.Eficiencia.linea)\
             .all()
    return [r[0] for r in rows]

@app.get("/api/eficiencias/processes")
def get_processes(db: Session = Depends(get_db)):
    rows = db.query(models.Eficiencia.proceso)\
             .distinct()\
             .order_by(models.Eficiencia.proceso)\
             .all()
    return [r[0] for r in rows]


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

from sqlalchemy import func

@app.get("/api/eficiencias/weekly")
def eficiencia_semanal_por_semana(
    start: date | None   = None,
    end:   date | None   = None,
    linea: str  | None   = None,
    proceso: str| None   = None,
    db: Session = Depends(get_db)
):
    # 1) Base de la query
    q = db.query(
        models.Eficiencia.semana.label("semana"),
        models.Eficiencia.proceso,
        func.avg(models.Eficiencia.eficiencia_asociado).label("promedio_asociado")
    )
    # 2) Si quieres aplicar filtros de fecha/linea/proceso:
    if start:   q = q.filter(models.Eficiencia.fecha >= start)
    if end:     q = q.filter(models.Eficiencia.fecha <= end)
    if linea:   q = q.filter(models.Eficiencia.linea == linea)
    if proceso: q = q.filter(models.Eficiencia.proceso == proceso)

    # 3) Agrupa por la columna semana en vez de la fecha
    q = q.group_by(models.Eficiencia.semana, models.Eficiencia.proceso) \
         .order_by(models.Eficiencia.semana)

    # 4) Devuelve JSON
    return [
        {"semana": int(sem), "proceso": proc, "promedio_asociado": float(round(avg,2))}
        for sem, proc, avg in q.all()
    ]


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

#topAsociadospEORES
@app.get("/api/eficiencias/top-associates")
def worst_associados(limit: int = 5, db: Session = Depends(get_db)):
    q = (
        db.query(
            models.Eficiencia.nombre_asociado.label("nombre"),
            func.avg(models.Eficiencia.eficiencia_asociado).label("promedio_asociado")
        )
        .group_by(models.Eficiencia.nombre_asociado)
        .order_by(func.avg(models.Eficiencia.eficiencia_asociado).asc())   # <<< ascendente
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

@app.get("/api/eficiencias/counts")
def conteo_sw_wd_por_linea(db: Session = Depends(get_db)):
    """
    Para cada línea, suma las piezas producidas por SW y WD.
    """
    q = (
        db.query(
            models.Eficiencia.linea.label("linea"),
            models.Eficiencia.tipo_proceso.label("tipo_proceso"),
            func.sum(models.Eficiencia.piezas).label("total_piezas")
        )
        .group_by(models.Eficiencia.linea, models.Eficiencia.tipo_proceso)
        .order_by(models.Eficiencia.linea)
    )
    return [
        {"linea": linea, "tipo_proceso": tp, "total_piezas": int(tpiezas)}
        for linea, tp, tpiezas in q.all()
    ]


@app.get("/api/eficiencias/weekly/downtime")
def downtime_weekly_by_line(
    start: date | None   = None,
    end:   date | None   = None,
    linea: str  | None   = None,
    proceso: str| None   = None,
    db: Session = Depends(get_db)
):
    # Base de la query: sumar tiempo_muerto
    q = db.query(
        models.Eficiencia.semana.label("semana"),
        models.Eficiencia.linea.label("linea"),
        func.avg(models.Eficiencia.tiempo_muerto).label("avg_downtime")
    )
    # filtros opcionales
    if start:   q = q.filter(models.Eficiencia.fecha >= start)
    if end:     q = q.filter(models.Eficiencia.fecha <= end)
    if linea:   q = q.filter(models.Eficiencia.linea == linea)
    if proceso: q = q.filter(models.Eficiencia.proceso == proceso)

    q = q.group_by(models.Eficiencia.semana, models.Eficiencia.linea) \
         .order_by(models.Eficiencia.semana)

    return [
        {
          "semana": int(sem),
          "linea": line,
          "avg_downtime": float(round(dt,2))
        }
        for sem, line, dt in q.all()
    ]
