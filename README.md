# TFG Monitor — Plataforma de Monitorización y Seguridad

## Requisitos previos
- Docker y Docker Compose
- Python 3.11+
- Node.js 20+ (para el frontend, más adelante)

---

## 1. Arrancar la base de datos

```bash
docker compose up -d
```

Esto levanta PostgreSQL en el puerto 5432 y ejecuta automáticamente `schema.sql`.

Verificar que está corriendo:
```bash
docker compose ps
```

---

## 2. Instalar dependencias del backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 3. Arrancar el backend

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

El backend queda disponible en:
- API: http://localhost:8000
- Documentación automática: http://localhost:8000/docs
- Health check: http://localhost:8000/health

---

## 4. Arrancar el agente (opcional, en otra terminal)

```bash
cd agente
pip install -r requirements.txt
SISTEMA_ID=<uuid-del-sistema> python agente.py
```

---

## Estructura del proyecto

```
tfg-monitor/
├── docker-compose.yml       # PostgreSQL
├── backend/
│   ├── .env                 # variables de entorno
│   ├── requirements.txt
│   ├── schema.sql           # script de creación de BD
│   └── app/
│       ├── main.py          # entrada FastAPI
│       ├── database.py      # conexión async PostgreSQL
│       ├── models/          # modelos SQLAlchemy
│       ├── schemas/         # modelos Pydantic
│       ├── routers/         # endpoints por recurso
│       └── core/
│           ├── config.py    # settings desde .env
│           └── security.py  # JWT y bcrypt
└── agente/
    ├── agente.py            # script de monitorización
    └── requirements.txt
```
