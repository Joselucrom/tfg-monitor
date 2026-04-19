from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime

from app.database import get_db
from app.models import Alerta, Recomendacion
from app.schemas import AlertaOut, RecomendacionOut
from app.routers.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=list[AlertaOut])
async def listar_alertas(
    resuelta: bool | None = Query(None),
    limite: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Lista alertas. Filtra por estado resuelto/pendiente si se indica."""
    q = select(Alerta).order_by(Alerta.timestamp.desc()).limit(limite)
    if resuelta is not None:
        q = q.where(Alerta.resuelta == resuelta)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{alerta_id}", response_model=AlertaOut)
async def obtener_alerta(
    alerta_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    alerta = await _get_or_404(db, alerta_id)
    return alerta


@router.post("/{alerta_id}/resolver", response_model=AlertaOut)
async def resolver_alerta(
    alerta_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Marca una alerta como resuelta."""
    alerta = await _get_or_404(db, alerta_id)
    if alerta.resuelta:
        raise HTTPException(status_code=400, detail="La alerta ya está resuelta")
    alerta.resuelta = True
    alerta.resuelta_at = datetime.utcnow()
    await db.commit()
    await db.refresh(alerta)
    return alerta


@router.get("/{alerta_id}/recomendaciones", response_model=list[RecomendacionOut])
async def obtener_recomendaciones(
    alerta_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Devuelve las recomendaciones asociadas a una alerta."""
    from app.models import alertas_recomendaciones
    alerta = await _get_or_404(db, alerta_id)

    result = await db.execute(
        select(Recomendacion)
        .join(
            alertas_recomendaciones,
            Recomendacion.id == alertas_recomendaciones.c.recomendacion_id,
        )
        .where(alertas_recomendaciones.c.alerta_id == alerta.id)
        .order_by(Recomendacion.prioridad)
    )
    return result.scalars().all()


async def _get_or_404(db: AsyncSession, alerta_id: UUID) -> Alerta:
    result = await db.execute(select(Alerta).where(Alerta.id == alerta_id))
    alerta = result.scalar_one_or_none()
    if not alerta:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    return alerta
