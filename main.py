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
