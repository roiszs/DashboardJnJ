from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from typing import Optional

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

# 2) Endpoints de lectura con filtros
@app.get("/api/eficiencias", response_model=list[schemas.Eficiencia])
def leer_eficiencias(
    start: Optional[date] = None,
    end: Optional[date] = None,
    linea: Optional[str] = None,
    proceso: Optional[str] = None,
    db: Session = Depends(get_db),
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

@app.get("/api/eficiencias/lines")
def get_lines(db: Session = Depends(get_db)):
    rows = (
        db.query(models.Eficiencia.linea)
          .distinct()
          .order_by(models.Eficiencia.linea)
          .all()
    )
    return [r[0] for r in rows]

@app.get("/api/eficiencias/processes")
def get_processes(db: Session = Depends(get_db)):
    rows = (
        db.query(models.Eficiencia.proceso)
          .distinct()
          .order_by(models.Eficiencia.proceso)
          .all()
    )
    return [r[0] for r in rows]

# 3) Creación y borrado
@app.post("/api/eficiencias", response_model=schemas.Eficiencia, status_code=201)
def crear_eficiencia(
    payload: schemas.EficienciaCreate,
    db: Session = Depends(get_db),
):
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

# 4) Monta estáticos y HTML
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=FileResponse)
def serve_dashboard():
    return "static/index.html"

@app.get("/add.html", response_class=FileResponse)
def serve_form():
    return "static/add.html"

# 5) Métricas

@app.get("/api/eficiencias/weekly")
def eficiencia_semanal_por_semana(
    start: Optional[date] = None,
    end: Optional[date] = None,
    linea: Optional[str] = None,
    proceso: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(
        models.Eficiencia.semana.label("semana"),
        models.Eficiencia.proceso.label("proceso"),
        func.avg(models.Eficiencia.eficiencia_asociado).label("promedio_asociado")
    )
    if start:
        q = q.filter(models.Eficiencia.fecha >= start)
    if end:
        q = q.filter(models.Eficiencia.fecha <= end)
    if linea:
        q = q.filter(models.Eficiencia.linea == linea)
    if proceso:
        q = q.filter(models.Eficiencia.proceso == proceso)

    q = q.group_by(models.Eficiencia.semana, models.Eficiencia.proceso) \
         .order_by(models.Eficiencia.semana)

    return [
        {"semana": int(sem), "proceso": proc, "promedio_asociado": float(round(avg, 2))}
        for sem, proc, avg in q.all()
    ]

@app.get("/api/eficiencias/daily/process")
def eficiencia_diaria_proceso(
    start: Optional[date] = None,
    end: Optional[date] = None,
    linea: Optional[str] = None,
    proceso: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(
        models.Eficiencia.fecha.label("fecha"),
        models.Eficiencia.proceso.label("proceso"),
        func.avg(models.Eficiencia.eficiencia_asociado).label("promedio_asociado")
    )
    if start:
        q = q.filter(models.Eficiencia.fecha >= start)
    if end:
        q = q.filter(models.Eficiencia.fecha <= end)
    if linea:
        q = q.filter(models.Eficiencia.linea == linea)
    if proceso:
        q = q.filter(models.Eficiencia.proceso == proceso)

    q = q.group_by(models.Eficiencia.fecha, models.Eficiencia.proceso) \
         .order_by(models.Eficiencia.fecha)

    return [
        {"fecha": f.isoformat(), "proceso": proc, "promedio_asociado": float(avg)}
        for f, proc, avg in q.all()
    ]

@app.get("/api/eficiencias/daily/line")
def eficiencia_diaria_linea(
    start: Optional[date] = None,
    end: Optional[date] = None,
    linea: Optional[str] = None,
    proceso: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(
        models.Eficiencia.fecha.label("fecha"),
        models.Eficiencia.linea.label("linea"),
        func.avg(models.Eficiencia.eficiencia_asociado).label("promedio_asociado")
    )
    if start:
        q = q.filter(models.Eficiencia.fecha >= start)
    if end:
        q = q.filter(models.Eficiencia.fecha <= end)
    if linea:
        q = q.filter(models.Eficiencia.linea == linea)
    if proceso:
        q = q.filter(models.Eficiencia.proceso == proceso)

    q = q.group_by(models.Eficiencia.fecha, models.Eficiencia.linea) \
         .order_by(models.Eficiencia.fecha)

    return [
        {"fecha": f.isoformat(), "linea": l, "promedio_asociado": float(avg)}
        for f, l, avg in q.all()
    ]

@app.get("/api/eficiencias/top-associates")
def worst_associados(
    start: Optional[date] = None,
    end: Optional[date] = None,
    linea: Optional[str] = None,
    proceso: Optional[str] = None,
    limit: int = 5,
    db: Session = Depends(get_db),
):
    sub = db.query(
        models.Eficiencia.nombre_asociado.label("nombre"),
        func.avg(models.Eficiencia.eficiencia_asociado).label("promedio_asociado")
    )
    if start:
        sub = sub.filter(models.Eficiencia.fecha >= start)
    if end:
        sub = sub.filter(models.Eficiencia.fecha <= end)
    if linea:
        sub = sub.filter(models.Eficiencia.linea == linea)
    if proceso:
        sub = sub.filter(models.Eficiencia.proceso == proceso)

    q = sub.group_by(models.Eficiencia.nombre_asociado) \
           .order_by(func.avg(models.Eficiencia.eficiencia_asociado).asc()) \
           .limit(limit)

    return [
        {"nombre": nombre, "promedio_asociado": float(round(prom, 2))}
        for nombre, prom in q.all()
    ]

@app.get("/api/eficiencias/shift")
def eficiencia_por_turno(
    start: Optional[date] = None,
    end: Optional[date] = None,
    linea: Optional[str] = None,
    proceso: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(
        models.Eficiencia.turno.label("turno"),
        func.avg(models.Eficiencia.eficiencia_asociado).label("promedio_asociado")
    )
    if start:
        q = q.filter(models.Eficiencia.fecha >= start)
    if end:
        q = q.filter(models.Eficiencia.fecha <= end)
    if linea:
        q = q.filter(models.Eficiencia.linea == linea)
    if proceso:
        q = q.filter(models.Eficiencia.proceso == proceso)

    q = q.group_by(models.Eficiencia.turno) \
         .order_by(models.Eficiencia.turno)

    return [
        {"turno": t, "promedio_asociado": float(round(p, 2))}
        for t, p in q.all()
    ]

@app.get("/api/eficiencias/counts")
def conteo_sw_wd_por_linea(
    start: Optional[date] = None,
    end: Optional[date] = None,
    linea: Optional[str] = None,
    proceso: Optional[str] = None,
    db: Session = Depends(get_db),
):
    sub = db.query(
        models.Eficiencia.linea.label("linea"),
        models.Eficiencia.tipo_proceso.label("tipo_proceso"),
        func.sum(models.Eficiencia.piezas).label("total_piezas")
    )
    if start:
        sub = sub.filter(models.Eficiencia.fecha >= start)
    if end:
        sub = sub.filter(models.Eficiencia.fecha <= end)
    if linea:
        sub = sub.filter(models.Eficiencia.linea == linea)
    if proceso:
        sub = sub.filter(models.Eficiencia.proceso == proceso)

    q = sub.group_by(models.Eficiencia.linea, models.Eficiencia.tipo_proceso) \
           .order_by(models.Eficiencia.linea)

    return [
        {"linea": linea, "tipo_proceso": tp, "total_piezas": int(tpz)}
        for linea, tp, tpz in q.all()
    ]

@app.get("/api/eficiencias/weekly/downtime")
def downtime_weekly_by_line(
    start: Optional[date] = None,
    end: Optional[date] = None,
    linea: Optional[str] = None,
    proceso: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(
        models.Eficiencia.semana.label("semana"),
        models.Eficiencia.linea.label("linea"),
        func.avg(models.Eficiencia.tiempo_muerto).label("avg_downtime")
    )
    if start:
        q = q.filter(models.Eficiencia.fecha >= start)
    if end:
        q = q.filter(models.Eficiencia.fecha <= end)
    if linea:
        q = q.filter(models.Eficiencia.linea == linea)
    if proceso:
        q = q.filter(models.Eficiencia.proceso == proceso)

    q = q.group_by(models.Eficiencia.semana, models.Eficiencia.linea) \
         .order_by(models.Eficiencia.semana)

    return [
        {"semana": int(sem), "linea": line, "avg_downtime": float(round(dt, 2))}
        for sem, line, dt in q.all()
    ]
