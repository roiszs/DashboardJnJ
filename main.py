# main.py
from collections import defaultdict
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
import models
from database import SessionLocal

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/api/eficiencias/weekly")
def eficiencia_semanal_iso(db: Session = Depends(get_db)):
    # 1) Trae todos los registros
    items = db.query(models.Eficiencia).all()

    # 2) Agrupa por (año, semana ISO, proceso) y calcula promedio de eficiencia del asociado
    grupos = defaultdict(list)
    for r in items:
        year, week, _ = r.fecha.isocalendar()        # .isocalendar() → (año, semana, díaDeSemana)
        key = (year, week, r.proceso)
        grupos[key].append(r.eficiencia_asociado)

    # 3) Construye la salida
    salida = []
    for (year, week, proceso), vals in grupos.items():
        salida.append({
            "semana": f"{year}-{week:02d}",           # ej. "2025-04"
            "proceso": proceso,
            "promedio_asociado": round(sum(vals)/len(vals), 2)
        })

    # 4) Ordénalo por año/semana
    salida.sort(key=lambda x: x["semana"])
    return salida
