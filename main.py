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
def leer_eficiencias(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Eficiencia).offset(skip).limit(limit).all()

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

@app.get("/api/eficiencias/weekly")
def eficiencia_semanal(db: Session = Depends(get_db)):
    query = (
        db.query(
            func.strftime("%Y-%W", models.Eficiencia.fecha).label("semana"),
            models.Eficiencia.proceso,
            func.avg(models.Eficiencia.eficiencia_linea).label("promedio_linea")
        )
        .group_by("semana", models.Eficiencia.proceso)
        .order_by("semana")
    )
    results = query.all()
    return [
        {"semana": semana, "proceso": proceso, "promedio_linea": float(prom)}
        for semana, proceso, prom in results
    ]
