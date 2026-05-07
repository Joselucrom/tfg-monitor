from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime

from app.database import get_db
from app.models import Alerta, Recomendacion, AlertaRecomendacion
from app.schemas import (
    AlertaOut, RecomendacionOut,
    AlertaRecomendacionOut, AlertaRecomendacionUpdate,
)
from app.routers.auth import get_current_user

router = APIRouter()


# ══════════════════════════════════════════════════════════
# Alertas
# ══════════════════════════════════════════════════════════

@router.get("/", response_model=list[AlertaOut])
async def listar_alertas(
    resuelta: bool | None = Query(None),
    severidad: str | None = Query(None),
    limite: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Lista alertas con filtros opcionales por estado y severidad."""
    q = select(Alerta).order_by(Alerta.timestamp.desc()).limit(limite)
    if resuelta is not None:
        q = q.where(Alerta.resuelta == resuelta)
    if severidad:
        q = q.where(Alerta.severidad == severidad)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{alerta_id}", response_model=AlertaOut)
async def obtener_alerta(
    alerta_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Devuelve el detalle de una alerta."""
    return await _get_or_404(db, alerta_id)


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
    alerta.resuelta    = True
    alerta.resuelta_at = datetime.utcnow()
    await db.commit()
    await db.refresh(alerta)
    return alerta


# ══════════════════════════════════════════════════════════
# Recomendaciones asociadas a una alerta
# ══════════════════════════════════════════════════════════

@router.get(
    "/{alerta_id}/recomendaciones",
    response_model=list[AlertaRecomendacionOut],
)
async def obtener_recomendaciones(
    alerta_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Devuelve las recomendaciones asociadas a una alerta,
    incluyendo si han sido aplicadas (clase de asociación).
    """
    await _get_or_404(db, alerta_id)
    result = await db.execute(
        select(AlertaRecomendacion)
        .where(AlertaRecomendacion.alerta_id == alerta_id)
        .order_by(AlertaRecomendacion.recomendacion_id)
    )
    return result.scalars().all()


@router.get(
    "/{alerta_id}/recomendaciones/{recomendacion_id}",
    response_model=AlertaRecomendacionOut,
)
async def obtener_recomendacion(
    alerta_id: UUID,
    recomendacion_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Devuelve el detalle de una recomendación concreta de una alerta."""
    ar = await _get_ar_or_404(db, alerta_id, recomendacion_id)
    return ar


@router.patch(
    "/{alerta_id}/recomendaciones/{recomendacion_id}",
    response_model=AlertaRecomendacionOut,
)
async def marcar_recomendacion(
    alerta_id: UUID,
    recomendacion_id: UUID,
    datos: AlertaRecomendacionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Marca una recomendación como aplicada o no aplicada.
    Registra la fecha si se marca como aplicada.
    """
    ar = await _get_ar_or_404(db, alerta_id, recomendacion_id)
    ar.aplicada = datos.aplicada
    ar.aplicada_at = datetime.utcnow() if datos.aplicada else None
    await db.commit()
    await db.refresh(ar)
    return ar


# ══════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════

async def _get_or_404(db: AsyncSession, alerta_id: UUID) -> Alerta:
    result = await db.execute(
        select(Alerta).where(Alerta.id == alerta_id)
    )
    alerta = result.scalar_one_or_none()
    if not alerta:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    return alerta


async def _get_ar_or_404(
    db: AsyncSession,
    alerta_id: UUID,
    recomendacion_id: UUID,
) -> AlertaRecomendacion:
    result = await db.execute(
        select(AlertaRecomendacion).where(
            AlertaRecomendacion.alerta_id        == alerta_id,
            AlertaRecomendacion.recomendacion_id == recomendacion_id,
        )
    )
    ar = result.scalar_one_or_none()
    if not ar:
        raise HTTPException(
            status_code=404,
            detail="Recomendación no encontrada para esta alerta"
        )
    return ar