from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from uuid import UUID
from datetime import datetime, timezone

from app.database import get_db
from app.models import Alerta, Recomendacion, AlertaRecomendacion
from app.schemas import (
    AlertaOut, RecomendacionOut,
    AlertaRecomendacionOut, AlertaRecomendacionUpdate,
)

from app.routers.auth import get_current_user
from app.core.gemini import analizar_alerta

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
    alerta.resuelta_at = datetime.now(timezone.utc)
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
    await _get_or_404(db, alerta_id)
    result = await db.execute(
        select(AlertaRecomendacion, Recomendacion)
        .join(Recomendacion, AlertaRecomendacion.recomendacion_id == Recomendacion.id)
        .where(AlertaRecomendacion.alerta_id == alerta_id)
        .order_by(Recomendacion.prioridad)
    )
    rows = result.all()
    return [
        {
            "alerta_id":        ar.alerta_id,
            "recomendacion_id": ar.recomendacion_id,
            "aplicada":         ar.aplicada,
            "aplicada_at":      ar.aplicada_at,
            "texto":            rec.texto,
            "tipo_alerta":      rec.tipo_alerta,
            "prioridad":        rec.prioridad,
        }
        for ar, rec in rows
    ]


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
    ar.aplicada_at = datetime.now(timezone.utc) if datos.aplicada else None
    await db.commit()
    await db.refresh(ar)
    return ar


@router.get("/{alerta_id}/gemini")
async def analisis_gemini(
    alerta_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    alerta = await _get_or_404(db, alerta_id)

    # Obtener el evento asociado
    result = await db.execute(
        text("""
            SELECT tipo, valor, origen, sistema_id
            FROM eventos_sistema
            WHERE id = :id
            UNION ALL
            SELECT tipo, valor, origen, null as sistema_id
            FROM eventos_web
            WHERE id = :id
        """),
        {"id": alerta.evento_id}
    )
    evento = result.mappings().first()

    nombre_sistema = None
    historial_valores = []
    alertas_recientes = 0

    if evento and evento.get("sistema_id"):
        # Nombre del sistema
        from app.models import Sistema
        res = await db.execute(
            select(Sistema).where(Sistema.id == evento["sistema_id"])
        )
        sistema = res.scalar_one_or_none()
        if sistema:
            nombre_sistema = sistema.nombre

        # Últimos 5 valores de esa métrica en ese sistema
        res_hist = await db.execute(
            text("""
                SELECT valor, timestamp
                FROM eventos_sistema
                WHERE sistema_id = :sid
                  AND tipo = :tipo
                  AND valor IS NOT NULL
                ORDER BY timestamp DESC
                LIMIT 5
            """),
            {"sid": evento["sistema_id"], "tipo": evento["tipo"]}
        )
        historial_valores = [
            {"valor": row.valor, "timestamp": row.timestamp}
            for row in res_hist.fetchall()
        ]

        # Número de alertas del mismo tipo en las últimas 24h
        res_alertas = await db.execute(
            text("""
                SELECT COUNT(*) as total
                FROM alertas a
                JOIN eventos_sistema e ON e.id = a.evento_id
                WHERE e.sistema_id = :sid
                  AND e.tipo = :tipo
                  AND a.timestamp > NOW() - INTERVAL '24 hours'
            """),
            {"sid": evento["sistema_id"], "tipo": evento["tipo"]}
        )
        alertas_recientes = res_alertas.scalar() or 0

    analisis = await analizar_alerta(
        tipo_evento      = evento["tipo"]  if evento else "otro",
        valor            = evento["valor"] if evento else None,
        severidad        = alerta.severidad.value,
        mensaje          = alerta.mensaje,
        nombre_sistema   = nombre_sistema,
        historial_valores = historial_valores,
        alertas_recientes = alertas_recientes,
    )

    return analisis


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