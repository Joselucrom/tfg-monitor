from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import auth, usuarios, sistemas, servicios_web, eventos, alertas, reglas

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.debug,
)

# CORS — permitir peticiones desde el frontend React en desarrollo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router,          prefix="/api/auth",          tags=["auth"])
app.include_router(usuarios.router,      prefix="/api/usuarios",      tags=["usuarios"])
app.include_router(sistemas.router,      prefix="/api/sistemas",      tags=["sistemas"])
app.include_router(servicios_web.router, prefix="/api/servicios-web", tags=["servicios_web"])
app.include_router(eventos.router,       prefix="/api/eventos",       tags=["eventos"])
app.include_router(alertas.router,       prefix="/api/alertas",       tags=["alertas"])
app.include_router(reglas.router,        prefix="/api/reglas",        tags=["reglas"])


@app.get("/")
async def root():
    return {"status": "ok", "app": settings.app_name}


@app.get("/health")
async def health():
    return {"status": "healthy"}
