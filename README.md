# DashboardJnJ
# Dashboard J&J – Eficiencias S&S

Pequeño sistema interno para cargar eficiencias por Excel y visualizar KPIs y gráficas (Chart.js) con autenticación JWT (FastAPI Users).

## Requisitos

- Python 3.11+ (probado con 3.11/3.12/3.13)
- Node no requerido (solo frontend estático)
- Base de datos: SQLite por defecto (configurable por env)

## Instalación

```bash
python -m venv venv
source venv/bin/activate           # Windows: venv\Scripts\activate
pip install -r requirements.txt
