"""
Configuración compartida de pytest para el proyecto TFG Monitor.

IMPORTANTE sobre asyncpg y event loops:
asyncpg vincula sus conexiones al event loop en el que se crearon.
pytest-asyncio puede crear un event loop distinto para cada test
función, por lo que reutilizar un engine (y por tanto sus conexiones)
entre tests provoca errores "attached to a different loop".

La solución adoptada es crear un ENGINE NUEVO en cada test (scope
"function", el scope por defecto de los fixtures), garantizando que
el engine y sus conexiones siempre pertenecen al loop del test en
curso. El coste de rendimiento es insignificante para una suite de
pruebas de TFG.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://tfg_user:tfg_pass@localhost:5432/tfg_monitor_test"
)

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text


TEST_DATABASE_URL = os.environ["DATABASE_URL"]


@pytest_asyncio.fixture
async def test_engine():
    """
    Engine async nuevo en cada test, ligado al event loop
    en el que se ejecuta ese test concreto.
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Limpia las tablas al principio de cada test usando este mismo engine
    async with engine.begin() as conn:
        await conn.execute(text("""
            TRUNCATE TABLE
                alertas_recomendaciones, alertas,
                eventos_sistema, eventos_web, eventos,
                metricas_snapshot, reglas,
                sistemas, servicios_web, usuarios
            CASCADE
        """))
        await conn.execute(text(
            "ALTER TABLE sistemas ADD COLUMN IF NOT EXISTS intervalo_s INT NOT NULL DEFAULT 30"
        ))
        await conn.execute(text(
            "ALTER TABLE servicios_web ADD COLUMN IF NOT EXISTS intervalo_s INT NOT NULL DEFAULT 60"
        ))

    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def client(test_engine):
    """
    Cliente HTTP asíncrono que llama a la app FastAPI con la
    dependencia get_db sobrescrita para usar el engine de test
    de este mismo test (mismo event loop garantizado).
    """
    from app.main import app
    from app.database import get_db

    session_factory = async_sessionmaker(bind=test_engine, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def db(test_engine):
    """Sesión de base de datos de test para preparar/consultar datos directamente."""
    session_factory = async_sessionmaker(bind=test_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session