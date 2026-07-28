import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from uuid import UUID, uuid4
from datetime import datetime, timezone

from app.database import get_db
from app.models import Alerta, Regla, Recomendacion, AlertaRecomendacion, Sistema, ServicioWeb
from app.schemas import (
    EventoSistemaCreate, EventoWebCreate,
    EventoSistemaOut, EventoWebOut,
)
from app.routers.auth import get_current_user

router = APIRouter()


@router.get("/sistema", response_model=list[EventoSistemaOut])
async def listar_eventos_sistema(
    sistema_id: UUID | None = None,
    limite: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    where = (
        "WHERE sistema_id = :sid AND sistema_id IN (SELECT id FROM sistemas WHERE usuario_id = :uid)"
        if sistema_id
        else "WHERE sistema_id IN (SELECT id FROM sistemas WHERE usuario_id = :uid)"
    )
    params = {"sid": sistema_id, "lim": limite, "uid": current_user.id}
    result = await db.execute(
        text(f"""
            SELECT id, sistema_id, tipo, valor, origen, proceso, pid, timestamp
            FROM eventos_sistema
            {where}
            ORDER BY timestamp DESC
            LIMIT :lim
        """), params
    )
    rows = result.mappings().all()
    return [dict(r) for r in rows]


@router.get("/web", response_model=list[EventoWebOut])
async def listar_eventos_web(
    servicio_web_id: UUID | None = None,
    limite: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    where = (
        "WHERE servicio_web_id = :sid AND servicio_web_id IN (SELECT id FROM servicios_web WHERE usuario_id = :uid)"
        if servicio_web_id
        else "WHERE servicio_web_id IN (SELECT id FROM servicios_web WHERE usuario_id = :uid)"
    )
    params = {"sid": servicio_web_id, "lim": limite, "uid": current_user.id}
    result = await db.execute(
        text(f"""
            SELECT id, servicio_web_id, tipo, valor, origen, http_status, tiempo_ms, timestamp
            FROM eventos_web
            {where}
            ORDER BY timestamp DESC
            LIMIT :lim
        """), params
    )
    rows = result.mappings().all()
    return [dict(r) for r in rows]


@router.post("/sistema", response_model=EventoSistemaOut, status_code=201)
async def recibir_evento_sistema(
    datos: EventoSistemaCreate,
    db: AsyncSession = Depends(get_db),
):
    evento_id = uuid4()
    now = datetime.now(timezone.utc)

    await db.execute(text("""
        INSERT INTO eventos_sistema
            (id, tipo, valor, origen, metadata, timestamp, sistema_id, proceso, pid)
        VALUES
            (:id, :tipo, :valor, :origen, :metadata, :timestamp, :sistema_id, :proceso, :pid)
    """), {
        "id":         evento_id,
        "tipo":       datos.tipo.value,
        "valor":      datos.valor,
        "origen":     datos.origen,
        "metadata":   json.dumps(datos.metadata) if datos.metadata else None,
        "timestamp":  now,
        "sistema_id": datos.sistema_id,
        "proceso":    datos.proceso,
        "pid":        datos.pid,
    })

    # Obtener usuario_id del sistema
    result = await db.execute(select(Sistema).where(Sistema.id == datos.sistema_id))
    sistema = result.scalar_one_or_none()
    usuario_id = sistema.usuario_id if sistema else None
    
    if sistema:
        sistema.ultimo_contacto = now

    await _evaluar_reglas_raw(db, evento_id, datos.tipo.value, datos.valor, datos.origen, usuario_id)
    await db.commit()

    return {
        "id":         evento_id,
        "sistema_id": datos.sistema_id,
        "tipo":       datos.tipo,
        "valor":      datos.valor,
        "origen":     datos.origen,
        "proceso":    datos.proceso,
        "pid":        datos.pid,
        "timestamp":  now,
    }


@router.post("/web", response_model=EventoWebOut, status_code=201)
async def recibir_evento_web(
    datos: EventoWebCreate,
    db: AsyncSession = Depends(get_db),
):
    evento_id = uuid4()
    now = datetime.now(timezone.utc)

    await db.execute(text("""
        INSERT INTO eventos_web
            (id, tipo, valor, origen, metadata, timestamp, servicio_web_id, http_status, tiempo_ms)
        VALUES
            (:id, :tipo, :valor, :origen, :metadata, :timestamp, :servicio_web_id, :http_status, :tiempo_ms)
    """), {
        "id":              evento_id,
        "tipo":            datos.tipo.value,
        "valor":           datos.valor,
        "origen":          datos.origen,
        "metadata":        json.dumps(datos.metadata) if datos.metadata else None,
        "timestamp":       now,
        "servicio_web_id": datos.servicio_web_id,
        "http_status":     datos.http_status,
        "tiempo_ms":       datos.tiempo_ms,
    })

    # Obtener usuario_id del servicio web
    result = await db.execute(select(ServicioWeb).where(ServicioWeb.id == datos.servicio_web_id))
    servicio_web = result.scalar_one_or_none()
    usuario_id = servicio_web.usuario_id if servicio_web else None

    await _evaluar_reglas_raw(db, evento_id, datos.tipo.value, datos.valor, datos.origen, usuario_id)
    await db.commit()

    return {
        "id":              evento_id,
        "servicio_web_id": datos.servicio_web_id,
        "tipo":            datos.tipo,
        "valor":           datos.valor,
        "origen":          datos.origen,
        "http_status":     datos.http_status,
        "tiempo_ms":       datos.tiempo_ms,
        "timestamp":       now,
    }


async def _evaluar_reglas_raw(
    db: AsyncSession,
    evento_id: UUID,
    tipo: str,
    valor: float | None,
    origen: str | None,
    usuario_id: UUID | None = None,
) -> None:
    if valor is None:
        return

    q = select(Regla).where(Regla.activa == True, Regla.metrica == tipo)
    if usuario_id:
        q = q.where(Regla.usuario_id == usuario_id)
    
    result = await db.execute(q)
    reglas = result.scalars().all()

    for regla in reglas:
        if _cumple_condicion(valor, regla.operador.value, regla.umbral):
            alerta = Alerta(
                evento_id = evento_id,
                regla_id  = regla.id,
                severidad = regla.severidad,
                mensaje   = (
                    f"[{regla.severidad.value.upper()}] {regla.nombre}: "
                    f"{tipo} = {valor} "
                    f"(umbral {regla.operador.value} {regla.umbral})"
                    f" — origen: {origen or 'desconocido'}"
                ),
            )
            db.add(alerta)
            await db.flush()
            await _asociar_recomendaciones(db, alerta, tipo)


def _cumple_condicion(valor: float, operador: str, umbral: float) -> bool:
    match operador:
        case ">":  return valor > umbral
        case "<":  return valor < umbral
        case ">=": return valor >= umbral
        case "<=": return valor <= umbral
        case "=":  return valor == umbral
        case _:    return False


async def _asociar_recomendaciones(
    db: AsyncSession, alerta: Alerta, tipo_alerta: str
) -> None:
    result = await db.execute(
        select(Recomendacion)
        .where(Recomendacion.tipo_alerta == tipo_alerta)
        .order_by(Recomendacion.prioridad)
    )
    for rec in result.scalars().all():
        # ON CONFLICT DO NOTHING evita duplicados si se llama dos veces
        await db.execute(
            text("""
                INSERT INTO alertas_recomendaciones
                    (alerta_id, recomendacion_id, aplicada)
                VALUES
                    (:alerta_id, :rec_id, false)
                ON CONFLICT (alerta_id, recomendacion_id) DO NOTHING
            """),
            {"alerta_id": alerta.id, "rec_id": rec.id}
        )