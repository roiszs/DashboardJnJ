from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoint de lectura que ya tenías
@app.get("/api/eficiencias", response_model=list[schemas.Eficiencia])
def leer_eficiencias(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Eficiencia).offset(skip).limit(limit).all()

# Nuevo endpoint para crear un registro manualmente
@app.post("/api/eficiencias", response_model=schemas.Eficiencia, status_code=201)
def crear_eficiencia(payload: schemas.EficienciaCreate, db: Session = Depends(get_db)):
    registro = models.Eficiencia(**payload.dict())
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return registro
