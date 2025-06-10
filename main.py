# main.py
from fastapi import FastAPI, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session

import models
from database import SessionLocal, engine
import schemas          # o bien: from schemas import Eficiencia, EficienciaCreate

# Crea tablas
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get(
    "/api/eficiencias",
    response_model=List[schemas.Eficiencia]      # aquí usa schemas.Eficiencia
)
def leer_eficiencias(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Eficiencia).offset(skip).limit(limit).all()

@app.post(
    "/api/eficiencias",
    response_model=schemas.Eficiencia,           # y aquí también
    status_code=201
)
def crear_eficiencia(
    payload: schemas.EficienciaCreate,
    db: Session = Depends(get_db)
):
    registro = models.Eficiencia(**payload.dict())
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return registro
