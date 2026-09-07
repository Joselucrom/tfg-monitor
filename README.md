# TFG Monitor

Plataforma web de monitorización y seguridad con análisis inteligente mediante IA.

Desarrollada como Trabajo Fin de Grado en la **Universidad de Cádiz**

---

## Descripción

TFG Monitor permite supervisar en tiempo real el estado de servidores y servicios web, detectar eventos anómalos automáticamente mediante un motor de reglas configurable, y obtener análisis inteligentes ante incidencias mediante la integración con la API de **Google Gemini**.

### Características principales

- **Dashboard en tiempo real** con métricas de CPU, RAM y disco y gráficas de evolución temporal
- **Motor de reglas automático** que genera alertas sin intervención manual
- **Análisis con IA** Gemini proporciona diagnóstico, causas probables y acciones recomendadas
- **Agente de monitorización** ligero en Python, configurable por variables de entorno
- **Checks HTTP** de disponibilidad y tiempo de respuesta de servicios web
- **Panel de administración** con estadísticas globales y gestión de usuarios
- **Dos roles** administrador y operador, con acceso diferenciado

---

## Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3.11, FastAPI, SQLAlchemy async, asyncpg |
| Base de datos | PostgreSQL 16 |
| Frontend | React 19 Tailwind CSS, Vite, Recharts |
| Agente | Python 3.11, psutil, httpx |
| IA | Google Gemini API (google-genai) |
| Despliegue | Docker, Docker Compose, Nginx |

---

## Estructura del repositorio

```
tfg-monitor/
├── backend/              # API REST (FastAPI)
│   ├── app/
│   │   ├── core/         # Configuración, seguridad, Gemini
│   │   ├── models/       # Modelos SQLAlchemy
│   │   ├── routers/      # Endpoints por recurso
│   │   └── schemas/      # Validación Pydantic
│   ├── schema.sql        # Script de creación de BD
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example      # Plantilla de variables de entorno
├── frontend/             # SPA React
│   ├── src/
│   │   ├── api/          # Cliente Axios con interceptores JWT
│   │   ├── components/   # Layout, gráficas reutilizables
│   │   ├── context/      # Contexto de autenticación
│   │   └── pages/        # Vistas de la aplicación
│   └── Dockerfile
├── agente/               # Script de monitorización
│   ├── agente.py
│   └── requirements.txt
├── tests/                # Suite de pruebas (58 tests)
│   ├── conftest.py
│   ├── test_motor_reglas.py
│   ├── test_gemini.py
│   ├── test_integracion_auth.py
│   └── test_integracion_flujo.py
├── docker-compose.yml
└── README.md
```

---

## Instalación y arranque

### Requisitos previos

- Docker y Docker Compose instalados
- Una clave de API de Google Gemini (gratuita en [aistudio.google.com](https://aistudio.google.com))

### Pasos

**1. Clonar el repositorio**

```bash
git clone https://github.com/usuario/tfg-monitor.git
cd tfg-monitor
```

**2. Configurar las variables de entorno**

```bash
cp backend/.env.example backend/.env
```

Edita `backend/.env` y rellena los valores:

```env
DATABASE_URL=postgresql+asyncpg://tfg_user:tfg_pass@db:5432/tfg_monitor
SECRET_KEY=cambia_esto_por_una_clave_segura
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
APP_NAME=TFG Monitor
DEBUG=False
GEMINI_API_KEY=tu_clave_de_gemini_aqui
```

**3. Levantar todos los servicios**

```bash
docker compose up --build -d
```

Esto levanta automáticamente:
- PostgreSQL con el schema inicializado
- Backend FastAPI en el puerto 8000
- Frontend React + Nginx en el puerto 80
- pgAdmin en el puerto 5050

**4. Abrir la aplicación**

Abre [http://localhost](http://localhost) en el navegador.

La primera vez, crea una cuenta de administrador desde la pantalla de login → "Crear cuenta".

---

## Instalar el agente en un servidor a monitorizar

El agente se ejecuta directamente en el servidor (sin Docker) para acceder a las métricas reales del sistema operativo.

```bash
# En el servidor a monitorizar
scp -r agente/ usuario@ip-servidor:/home/usuario/tfg-agente
ssh usuario@ip-servidor
cd tfg-agente
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

export SISTEMA_ID="uuid-del-sistema-registrado-en-la-plataforma"
export BACKEND_URL="http://ip-del-servidor-principal:8000"
export INTERVALO=30
export UMBRAL_CPU=85
export UMBRAL_RAM=85
export UMBRAL_DISCO=85

python agente.py
```

El UUID del sistema se obtiene desde la propia plataforma: Sistemas → Instalar agente.

---

## Ejecutar las pruebas

```bash
# Instalar dependencias de test
pip install pytest pytest-asyncio httpx

# Crear BD de test
docker exec -it tfg_postgres psql -U tfg_user -d tfg_monitor \
  -c "CREATE DATABASE tfg_monitor_test;"
docker exec -i tfg_postgres psql -U tfg_user -d tfg_monitor_test \
  < backend/schema.sql

# Ejecutar suite completa (58 tests)
pytest tests/ -v
```

---

## Documentación de la API

Con el backend en marcha, la documentación interactiva está disponible en:

```
http://localhost:8000/docs
```

---

## Administración de la base de datos

pgAdmin 4 está disponible en [http://localhost:5050](http://localhost:5050)

- **Email:** admin@admin.com
- **Password:** admin
- **Host de conexión:** db
- **Puerto:** 5432
- **Usuario BD:** tfg_user
- **Password BD:** tfg_pass