from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
import pandas as pd
import io, re
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
    start:   Optional[date] = None,
    end:     Optional[date] = None,
    linea:   Optional[str]  = None,
    proceso: Optional[str]  = None,
    limit:   int            = 5,
    db:      Session        = Depends(get_db),
):
    # 1) Base query
    q = db.query(models.Eficiencia)

    # 2) Aplica filtros si vienen
    if start:
        q = q.filter(models.Eficiencia.fecha >= start)
    if end:
        q = q.filter(models.Eficiencia.fecha <= end)
    if linea:
        q = q.filter(models.Eficiencia.linea == linea)
    if proceso:
        q = q.filter(models.Eficiencia.proceso == proceso)

    # 3) Agrupa por asociado y calcula avg, ordena ascendente (los peores primero)
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

@app.post("/api/eficiencias/upload")
async def upload_eficiencias(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # 1) Extensión
    if not file.filename.lower().endswith(('.xls', '.xlsx')):
        raise HTTPException(400, "Sube un archivo .xls o .xlsx")

    contents = await file.read()

    try:
        sheets = pd.read_excel(io.BytesIO(contents), sheet_name=None)
    except Exception as e:
        raise HTTPException(400, f"Error leyendo el Excel: {e}")

    frames = []
    for sheet_name, df in sheets.items():
        # --- A) Semana desde el nombre de la hoja ---
        m = re.search(r'(\d{1,2})', sheet_name)
        if not m:
            raise HTTPException(400, f"No encontré número de semana en la hoja '{sheet_name}'")
        semana_val = int(m.group(1))

        # --- B) Normaliza headers ---
        df.columns = [c.strip().lower() for c in df.columns]

        # --- C) Columnas requeridas mínimas ---
        required = {
            'nombre_asociado','linea','supervisor',
            'tipo_proceso','proceso','piezas',
            'eficiencia_asociado','turno'
        }
        faltan = required - set(df.columns)
        if faltan:
            raise HTTPException(400, f"Faltan columnas en '{sheet_name}': {', '.join(faltan)}")

        # --- D) Opcionales: crea si faltan ---
        if 'wwid' not in df.columns:           df['wwid'] = None
        if 'tiempo_muerto' not in df.columns:  df['tiempo_muerto'] = None
        if 'fecha' not in df.columns:          df['fecha'] = None  # la pondremos por default

        # --- E) Setea semana y tipos seguros ---
        df['semana'] = semana_val
        df['piezas'] = pd.to_numeric(df['piezas'], errors='coerce').fillna(0).astype(int)
        df['eficiencia_asociado'] = pd.to_numeric(df['eficiencia_asociado'], errors='coerce').fillna(0.0)
        df['tiempo_muerto'] = pd.to_numeric(df['tiempo_muerto'], errors='coerce')
       # Convertir 'fecha' si existe
        if 'fecha' in df.columns:
            df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce').dt.date
        else:
            df['fecha'] = None  # si no viene en el archivo
            
            print(f"[upload] hojas procesadas: {len(frames)}")
            if not frames:
                return {"insertados": 0}

    big_df = pd.concat(frames, ignore_index=True)

    if not frames:
        return {"insertados": 0}

    # Intentamos concatenar; si falla, devolvemos 0 insertados
    try:
        big_df = pd.concat(frames, ignore_index=True)
    except ValueError:
        return {"insertados": 0}

    # … aquí sigue el resto tal cual lo tenías …
    allowed_cols = {c.name for c in models.Eficiencia.__table__.columns}
    registros = []
    for row in big_df.to_dict(orient='records'):
        clean = {k: v for k, v in row.items() if k in allowed_cols}
        registros.append(models.Eficiencia(**clean))

    try:
        db.bulk_save_objects(registros)
        db.commit()
    except Exception as e:
        db.rollback()
        print("ERROR al insertar:", e)
        raise HTTPException(500, "Error insertando en BD. Revisa la terminal para detalles.")

    return {"insertados": len(registros)}