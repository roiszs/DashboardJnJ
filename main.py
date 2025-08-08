# main.py

from fastapi import (
    FastAPI, APIRouter, Depends,
    HTTPException, status, File, UploadFile
)
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
import pandas as pd
import io, re

from datetime import date
from typing import Optional

import models, schemas
from database import engine, SessionLocal 
from fastapi import FastAPI
from contextlib import asynccontextmanager
import models
from database import engine

from auth import (
    fastapi_users,
    auth_backend,
    get_current_active_user,
    get_current_active_admin,
    UserRead, UserCreate, UserUpdate, 
)

# 1) Instancia de FastAPI
# 2) Evento de arranque: crea todas las tablas (usuarios + eficiencias)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    models.Base.metadata.create_all(bind=engine)
    yield
    # shutdown (si necesitas cerrar algo)
app = FastAPI(title="Dashboard J&J")

# 3) Monta los estáticos (CSS, JS, imágenes)
app.mount("/static", StaticFiles(directory="static"), name="static")

# 4) Routers de autenticación (FastAPI-Users)
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),  # <—
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),     # <—
    prefix="/users",
    tags=["users"],
)

# 5) Páginas HTML
@app.get("/login.html", response_class=FileResponse)
def serve_login():
    return "static/login.html"

@app.get(
    "/",
    response_class=FileResponse,
    dependencies=[Depends(get_current_active_user)],
)
def serve_dashboard():
    return "static/index.html"

@app.get(
    "/add.html",
    response_class=FileResponse,
    dependencies=[Depends(get_current_active_user)],
)
def serve_form():
    return "static/add.html"

# 6) Dependencia para obtener la sesión de BD
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 7) APIRouter para todas las rutas /api/eficiencias
router = APIRouter(prefix="/api/eficiencias", tags=["eficiencias"])

# 7.1) Crear nuevo registro (solo admin)
@router.post(
    "",
    response_model=schemas.Eficiencia,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_active_admin)],
)
def crear_eficiencia(
    payload: schemas.EficienciaCreate,
    db: Session = Depends(get_db),
):
    registro = models.Eficiencia(**payload.dict())
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return registro

# 7.2) Borrar registro (solo admin)
@router.delete(
    "/{ef_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_current_active_admin)],
)
def borrar_eficiencia(
    ef_id: int,
    db: Session = Depends(get_db),
):
    reg = db.query(models.Eficiencia).filter(models.Eficiencia.id == ef_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    db.delete(reg)
    db.commit()

# 7.3) Leer registros con filtros y paginación (admin o viewer)
@router.get(
    "",
    response_model=list[schemas.Eficiencia],
    dependencies=[Depends(get_current_active_user)],
)
def leer_eficiencias(
    start:   Optional[date] = None,
    end:     Optional[date] = None,
    linea:   Optional[str]  = None,
    proceso: Optional[str]  = None,
    skip:    int            = 0,
    limit:   int            = 100,
    db:      Session        = Depends(get_db),
):
    try:
        q = db.query(models.Eficiencia)
        if start:   q = q.filter(models.Eficiencia.fecha >= start)
        if end:     q = q.filter(models.Eficiencia.fecha <= end)
        if linea:   q = q.filter(models.Eficiencia.linea == linea)
        if proceso: q = q.filter(models.Eficiencia.proceso == proceso)
        recientes = (
            q.order_by(models.Eficiencia.id.desc())
             .offset(skip)
             .limit(limit)
             .all()
        )
        return list(reversed(recientes))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 7.4) Endpoints auxiliares de filtros (admin o viewer)
@router.get("/lines", dependencies=[Depends(get_current_active_user)])
def get_lines(db: Session = Depends(get_db)):
    try:
        rows = (
            db.query(models.Eficiencia.linea)
              .distinct()
              .order_by(models.Eficiencia.linea)
              .all()
        )
        return [r[0] for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/processes", dependencies=[Depends(get_current_active_user)])
def get_processes(db: Session = Depends(get_db)):
    try:
        rows = (
            db.query(models.Eficiencia.proceso)
              .distinct()
              .order_by(models.Eficiencia.proceso)
              .all()
        )
        return [r[0] for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 8) Métricas (admin o viewer)
@router.get("/weekly", dependencies=[Depends(get_current_active_user)])
def eficiencia_semanal_por_semana(
    start:   Optional[date] = None,
    end:     Optional[date] = None,
    linea:   Optional[str]  = None,
    proceso: Optional[str]  = None,
    db:      Session        = Depends(get_db),
):
    try:
        q = db.query(
            models.Eficiencia.semana.label("semana"),
            models.Eficiencia.proceso.label("proceso"),
            func.avg(models.Eficiencia.eficiencia_asociado).label("promedio_asociado")
        )
        if start:   q = q.filter(models.Eficiencia.fecha >= start)
        if end:     q = q.filter(models.Eficiencia.fecha <= end)
        if linea:   q = q.filter(models.Eficiencia.linea == linea)
        if proceso: q = q.filter(models.Eficiencia.proceso == proceso)
        q = (
            q.group_by(models.Eficiencia.semana, models.Eficiencia.proceso)
             .order_by(models.Eficiencia.semana)
        )
        return [
            {"semana": int(sem), "proceso": proc, "promedio_asociado": float(round(avg, 2))}
            for sem, proc, avg in q.all()
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/daily/process", dependencies=[Depends(get_current_active_user)])
def eficiencia_diaria_proceso(
    start:   Optional[date] = None,
    end:     Optional[date] = None,
    linea:   Optional[str]  = None,
    proceso: Optional[str]  = None,
    db:      Session        = Depends(get_db),
):
    try:
        q = db.query(
            models.Eficiencia.fecha.label("fecha"),
            models.Eficiencia.proceso.label("proceso"),
            func.avg(models.Eficiencia.eficiencia_asociado).label("promedio_asociado")
        )
        if start:   q = q.filter(models.Eficiencia.fecha >= start)
        if end:     q = q.filter(models.Eficiencia.fecha <= end)
        if linea:   q = q.filter(models.Eficiencia.linea == linea)
        if proceso: q = q.filter(models.Eficiencia.proceso == proceso)
        q = (
            q.group_by(models.Eficiencia.fecha, models.Eficiencia.proceso)
             .order_by(models.Eficiencia.fecha)
        )
        return [
            {"fecha": f.isoformat(), "proceso": proc, "promedio_asociado": float(avg)}
            for f, proc, avg in q.all()
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/daily/line", dependencies=[Depends(get_current_active_user)])
def eficiencia_diaria_linea(
    start:   Optional[date] = None,
    end:     Optional[date] = None,
    linea:   Optional[str]  = None,
    proceso: Optional[str]  = None,
    db:      Session        = Depends(get_db),
):
    try:
        q = db.query(
            models.Eficiencia.fecha.label("fecha"),
            models.Eficiencia.linea.label("linea"),
            func.avg(models.Eficiencia.eficiencia_asociado).label("promedio_asociado")
        )
        if start:   q = q.filter(models.Eficiencia.fecha >= start)
        if end:     q = q.filter(models.Eficiencia.fecha <= end)
        if linea:   q = q.filter(models.Eficiencia.linea == linea)
        if proceso: q = q.filter(models.Eficiencia.proceso == proceso)
        q = (
            q.group_by(models.Eficiencia.fecha, models.Eficiencia.linea)
             .order_by(models.Eficiencia.fecha)
        )
        return [
            {"fecha": f.isoformat(), "linea": l, "promedio_asociado": float(avg)}
            for f, l, avg in q.all()
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/top-associates", dependencies=[Depends(get_current_active_user)])
def worst_associados(
    start:   Optional[date] = None,
    end:     Optional[date] = None,
    linea:   Optional[str]  = None,
    proceso: Optional[str]  = None,
    limit:   int            = 5,
    db:      Session        = Depends(get_db),
):
    try:
        q = db.query(models.Eficiencia)
        if start:   q = q.filter(models.Eficiencia.fecha >= start)
        if end:     q = q.filter(models.Eficiencia.fecha <= end)
        if linea:   q = q.filter(models.Eficiencia.linea == linea)
        if proceso: q = q.filter(models.Eficiencia.proceso == proceso)
        q2 = (
            q.with_entities(
                models.Eficiencia.nombre_asociado.label("nombre"),
                func.avg(models.Eficiencia.eficiencia_asociado).label("promedio_asociado")
            )
            .group_by(models.Eficiencia.nombre_asociado)
            .order_by(func.avg(models.Eficiencia.eficiencia_asociado).asc())
            .limit(limit)
        )
        return [
            {"nombre": nombre, "promedio_asociado": float(round(prom, 2))}
            for nombre, prom in q2.all()
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/shift", dependencies=[Depends(get_current_active_user)])
def eficiencia_por_turno(
    start:   Optional[date] = None,
    end:     Optional[date] = None,
    linea:   Optional[str]  = None,
    proceso: Optional[str]  = None,
    db:      Session        = Depends(get_db),
):
    try:
        q = db.query(
            models.Eficiencia.turno.label("turno"),
            func.avg(models.Eficiencia.eficiencia_asociado).label("promedio_asociado")
        )
        if start:   q = q.filter(models.Eficiencia.fecha >= start)
        if end:     q = q.filter(models.Eficiencia.fecha <= end)
        if linea:   q = q.filter(models.Eficiencia.linea == linea)
        if proceso: q = q.filter(models.Eficiencia.proceso == proceso)
        q = (
            q.group_by(models.Eficiencia.turno)
             .order_by(models.Eficiencia.turno)
        )
        return [
            {"turno": t, "promedio_asociado": float(round(p, 2))}
            for t, p in q.all()
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/counts", dependencies=[Depends(get_current_active_user)])
def conteo_sw_wd_por_linea(
    start:   Optional[date] = None,
    end:     Optional[date] = None,
    linea:   Optional[str]  = None,
    proceso: Optional[str]  = None,
    db:      Session        = Depends(get_db),
):
    try:
        sub = db.query(
            models.Eficiencia.linea.label("linea"),
            models.Eficiencia.tipo_proceso.label("tipo_proceso"),
            func.sum(models.Eficiencia.piezas).label("total_piezas")
        )
        if start:   sub = sub.filter(models.Eficiencia.fecha >= start)
        if end:     sub = sub.filter(models.Eficiencia.fecha <= end)
        if linea:   sub = sub.filter(models.Eficiencia.linea == linea)
        if proceso: sub = sub.filter(models.Eficiencia.proceso == proceso)
        q = (
            sub.group_by(models.Eficiencia.linea, models.Eficiencia.tipo_proceso)
               .order_by(models.Eficiencia.linea)
        )
        return [
            {"linea": linea, "tipo_proceso": tp, "total_piezas": int(tpz)}
            for linea, tp, tpz in q.all()
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/weekly/downtime", dependencies=[Depends(get_current_active_user)])
def downtime_weekly_by_line(
    start:   Optional[date] = None,
    end:     Optional[date] = None,
    linea:   Optional[str]  = None,
    proceso: Optional[str]  = None,
    db:      Session        = Depends(get_db),
):
    try:
        q = db.query(
            models.Eficiencia.semana.label("semana"),
            models.Eficiencia.linea.label("linea"),
            func.avg(models.Eficiencia.tiempo_muerto).label("avg_downtime")
        )
        if start:   q = q.filter(models.Eficiencia.fecha >= start)
        if end:     q = q.filter(models.Eficiencia.fecha <= end)
        if linea:   q = q.filter(models.Eficiencia.linea == linea)
        if proceso: q = q.filter(models.Eficiencia.proceso == proceso)
        q = (
            q.group_by(models.Eficiencia.semana, models.Eficiencia.linea)
             .order_by(models.Eficiencia.semana)
        )
        return [
            {"semana": int(sem), "linea": line, "avg_downtime": float(round(dt, 2))}
            for sem, line, dt in q.all()
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 9) Subida masiva desde Excel (solo admin)
@router.post("/upload", dependencies=[Depends(get_current_active_admin)])
async def upload_eficiencias(
    file: UploadFile = File(...),
    db:   Session    = Depends(get_db),
):
    if not file.filename.lower().endswith(('.xls', '.xlsx')):
        raise HTTPException(400, "Sube un archivo .xls o .xlsx")
    contents = await file.read()
    try:
        sheets = pd.read_excel(io.BytesIO(contents), sheet_name=None)
    except Exception as e:
        raise HTTPException(400, f"Error leyendo el Excel: {e}")

    frames: list[pd.DataFrame] = []
    for sheet_name, df in sheets.items():
        m = re.search(r'(\d{1,2})', sheet_name)
        if not m:
            raise HTTPException(400, f"No encontré número de semana en la hoja '{sheet_name}'")
        semana_val = int(m.group(1))
        df.columns = [c.strip().lower() for c in df.columns]
        required = {
            'nombre_asociado','linea','supervisor',
            'tipo_proceso','proceso','piezas',
            'eficiencia_asociado','turno'
        }
        faltan = required - set(df.columns)
        if faltan:
            raise HTTPException(400, f"Faltan columnas en '{sheet_name}': {', '.join(faltan)}")
        for opt in ('wwid','tiempo_muerto','fecha'):
            if opt not in df.columns:
                df[opt] = None
        df['semana'] = semana_val
        df['piezas'] = pd.to_numeric(df['piezas'], errors='coerce').fillna(0).astype(int)
        df['eficiencia_asociado'] = pd.to_numeric(df['eficiencia_asociado'], errors='coerce').fillna(0.0)
        df['tiempo_muerto'] = pd.to_numeric(df['tiempo_muerto'], errors='coerce')
        if 'fecha' in df.columns:
            df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce').dt.date
        frames.append(df)

    if not frames:
        return {"insertados": 0}

    big_df = pd.concat(frames, ignore_index=True)
    allowed_cols = {c.name for c in models.Eficiencia.__table__.columns}

    registros = [
        models.Eficiencia(**{k: v for k, v in row.items() if k in allowed_cols})
        for row in big_df.to_dict(orient='records')
    ]
    try:
        db.bulk_save_objects(registros)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(500, "Error insertando en BD. Revisa logs para más detalles.")

    return {"insertados": len(registros)}

# 10) Finalmente, monta el router principal
app.include_router(router)
