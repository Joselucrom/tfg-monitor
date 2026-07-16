from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime, timezone

from app.database import get_db
from app.models import MetricaSnapshot, Sistema
from app.schemas import MetricaSnapshotCreate, MetricaSnapshotOut
from app.routers.auth import get_current_user
from datetime import datetime, timedelta, timezone
from fastapi import Query

router = APIRouter()

@router.get("/historico/{sistema_id}", response_model=list[MetricaSnapshotOut])
async def historico_sistema(
    sistema_id: UUID,
    minutos: int = Query(60, description="Ventana de tiempo en minutos (30, 60, 1440)"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Devuelve los snapshots de un sistema en la ventana de tiempo indicada.
    Usado por las gráficas del dashboard y la vista de sistemas.
    """
    desde = datetime.now(timezone.utc) - timedelta(minutes=minutos)
    result = await db.execute(
        select(MetricaSnapshot)
        .where(
            MetricaSnapshot.sistema_id == sistema_id,
            MetricaSnapshot.timestamp >= desde,
        )
        .order_by(MetricaSnapshot.timestamp.asc())
    )
    return result.scalars().all()

@router.get("/", response_model=list[MetricaSnapshotOut])
async def listar_snapshots(
    sistema_id: UUID | None = None,
    limite: int = Query(100, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Lista snapshots de métricas. Filtra por sistema si se indica."""
    q = (
        select(MetricaSnapshot)
        .order_by(MetricaSnapshot.timestamp.desc())
        .limit(limite)
    )
    if sistema_id:
        q = q.where(MetricaSnapshot.sistema_id == sistema_id)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/ultimo/{sistema_id}", response_model=MetricaSnapshotOut)
async def ultimo_snapshot(
    sistema_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Devuelve el snapshot más reciente de un sistema."""
    result = await db.execute(
        select(MetricaSnapshot)
        .where(MetricaSnapshot.sistema_id == sistema_id)
        .order_by(MetricaSnapshot.timestamp.desc())
        .limit(1)
    )
    snapshot = result.scalar_one_or_none()
    if not snapshot:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="No hay snapshots para este sistema")
    return snapshot


@router.post("/", response_model=MetricaSnapshotOut, status_code=201)
async def guardar_snapshot(
    datos: MetricaSnapshotCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    El agente envía un snapshot periódico de métricas aquí.
    No requiere JWT — en producción usar API key.
    """
    snapshot = MetricaSnapshot(
        sistema_id    = datos.sistema_id,
        cpu_percent   = datos.cpu_percent,
        ram_percent   = datos.ram_percent,
        disco_percent = datos.disco_percent,
    )
    db.add(snapshot)

    # Actualizar ultimo_contacto del sistema
    result = await db.execute(
        select(Sistema).where(Sistema.id == datos.sistema_id)
    )
    sistema = result.scalar_one_or_none()
    if sistema:
        sistema.ultimo_contacto = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(snapshot)
    return snapshot