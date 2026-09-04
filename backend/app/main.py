import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.core.config import settings
from app.database import AsyncSessionLocal, engine
from app.routers import (
    auth, usuarios, sistemas, servicios_web,
    eventos, alertas, reglas, metricas, admin
)


async def ensure_database_schema() -> None:
    """Asegura que la base de datos tenga las columnas necesarias."""
    async with engine.begin() as conn:
        await conn.execute(text(
            "ALTER TABLE sistemas ADD COLUMN IF NOT EXISTS intervalo_s INT NOT NULL DEFAULT 30"
        ))
        await conn.execute(text(
            "ALTER TABLE servicios_web ADD COLUMN IF NOT EXISTS intervalo_s INT NOT NULL DEFAULT 60"
        ))


async def tarea_verificar_agentes():
    """Tarea de fondo que verifica agentes caídos cada 5 minutos."""
    from app.routers.sistemas import verificar_agentes_caidos_interno

    await asyncio.sleep(60)  # espera inicial al arrancar
    while True:
        try:
            async with AsyncSessionLocal() as db:
                await verificar_agentes_caidos_interno(db)
        except Exception as e:
            print(f"Error en tarea verificar agentes: {e}")
        await asyncio.sleep(300)  # cada 5 minutos


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_database_schema()
    task = asyncio.create_task(tarea_verificar_agentes())
    yield
    task.cancel()


app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server (default port)
        "http://localhost:5174",  # Vite alternative port
        "http://localhost:3000",  # Alternative dev port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(auth.router,          prefix="/api/auth",          tags=["auth"])
app.include_router(usuarios.router,      prefix="/api/usuarios",      tags=["usuarios"])
app.include_router(sistemas.router,      prefix="/api/sistemas",      tags=["sistemas"])
app.include_router(servicios_web.router, prefix="/api/servicios-web", tags=["servicios_web"])
app.include_router(metricas.router,      prefix="/api/metricas",      tags=["metricas"])
app.include_router(eventos.router,       prefix="/api/eventos",       tags=["eventos"])
app.include_router(alertas.router,       prefix="/api/alertas",       tags=["alertas"])
app.include_router(reglas.router,        prefix="/api/reglas",        tags=["reglas"])
app.include_router(admin.router,         prefix="/api/admin",         tags=["admin"])


@app.get("/")
async def root():
    return {"status": "ok", "app": settings.app_name, "version": "0.2.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}