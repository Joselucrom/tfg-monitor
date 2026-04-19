from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime

from app.database import get_db
from app.models import Evento, Alerta, Regla, Recomendacion, Sistema, ServicioWeb
from app.schemas import EventoCreate, EventoOut, AlertaOut
from app.routers.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=list[EventoOut])
async def listar_eventos(
    limite: int = Query(100, le=500),
    sistema_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Lista los últimos eventos. Filtra por sistema si se indica."""
    q = select(Evento).order_by(Evento.timestamp.desc()).limit(limite)
    if sistema_id:
        q = q.where(Evento.sistema_id == sistema_id)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/", response_model=EventoOut, status_code=201)
async def recibir_evento(
    datos: EventoCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint público para que el agente envíe eventos.
    No requiere autenticación JWT para facilitar el envío desde el agente.
    En producción se añadiría autenticación por API key.
    """
    evento = Evento(**datos.model_dump())
    db.add(evento)
    await db.flush()  # obtenemos el ID sin hacer commit aún

    # ── Motor de reglas ───────────────────────────────────
    await _evaluar_reglas(db, evento)

    # Actualizar ultimo_contacto del sistema si aplica
    if evento.sistema_id:
        result = await db.execute(
            select(Sistema).where(Sistema.id == evento.sistema_id)
        )
        sistema = result.scalar_one_or_none()
        if sistema:
            sistema.ultimo_contacto = datetime.utcnow()

    await db.commit()
    await db.refresh(evento)
    return evento


@router.get("/{evento_id}", response_model=EventoOut)
async def obtener_evento(
    evento_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Evento).where(Evento.id == evento_id))
    evento = result.scalar_one_or_none()
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return evento


# ── Motor de reglas ───────────────────────────────────────

async def _evaluar_reglas(db: AsyncSession, evento: Evento) -> None:
    """
    Evalúa todas las reglas activas contra el evento recibido.
    Si alguna se cumple, genera una Alerta y asocia recomendaciones.
    """
    if evento.valor is None:
        return

    result = await db.execute(
        select(Regla).where(
            Regla.activa == True,
            Regla.metrica == evento.tipo.value,
        )
    )
    reglas = result.scalars().all()

    for regla in reglas:
        if _cumple_condicion(evento.valor, regla.operador.value, regla.umbral):
            alerta = Alerta(
                evento_id=evento.id,
                regla_id=regla.id,
                severidad=regla.severidad,
                mensaje=_generar_mensaje(evento, regla),
            )
            db.add(alerta)
            await db.flush()

            # Asociar recomendaciones del catálogo
            await _asociar_recomendaciones(db, alerta, evento.tipo.value)


def _cumple_condicion(valor: float, operador: str, umbral: float) -> bool:
    match operador:
        case ">":  return valor > umbral
        case "<":  return valor < umbral
        case ">=": return valor >= umbral
        case "<=": return valor <= umbral
        case "=":  return valor == umbral
        case _:    return False


def _generar_mensaje(evento: Evento, regla: Regla) -> str:
    return (
        f"[{regla.severidad.value.upper()}] {regla.nombre}: "
        f"{evento.tipo.value} = {evento.valor} "
        f"(umbral {regla.operador.value} {regla.umbral})"
        f" — origen: {evento.origen or 'desconocido'}"
    )


async def _asociar_recomendaciones(
    db: AsyncSession, alerta: Alerta, tipo_alerta: str
) -> None:
    from app.models import alertas_recomendaciones  # importación local para evitar circular
    result = await db.execute(
        select(Recomendacion).where(Recomendacion.tipo_alerta == tipo_alerta)
        .order_by(Recomendacion.prioridad)
    )
    recomendaciones = result.scalars().all()
    for rec in recomendaciones:
        await db.execute(
            alertas_recomendaciones.insert().values(
                alerta_id=alerta.id,
                recomendacion_id=rec.id,
            )
        )
