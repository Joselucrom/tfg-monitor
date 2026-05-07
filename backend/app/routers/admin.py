from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, date

from app.database import get_db
from app.models import (
    Usuario, Sistema, ServicioWeb,
    Alerta, EventoSistema, Regla, RolUsuario
)
from app.schemas import EstadisticasGlobales, SistemaTop, ReglaTop
from app.routers.auth import get_current_user

router = APIRouter()


# ══════════════════════════════════════════════════════════
# Dependencia: verificar rol admin
# ══════════════════════════════════════════════════════════

async def require_admin(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    """Lanza 403 si el usuario no tiene rol admin."""
    if current_user.rol != RolUsuario.admin:
        raise HTTPException(
            status_code=403,
            detail="Acceso restringido a administradores"
        )
    return current_user


# ══════════════════════════════════════════════════════════
# Estadísticas globales
# ══════════════════════════════════════════════════════════

@router.get("/estadisticas", response_model=EstadisticasGlobales)
async def estadisticas_globales(
    db: AsyncSession = Depends(get_db),
    admin: Usuario = Depends(require_admin),
):
    """Resumen global de uso de la plataforma."""
    total_usuarios      = await _count(db, Usuario)
    total_sistemas      = await _count(db, Sistema)
    total_servicios_web = await _count(db, ServicioWeb)
    total_alertas       = await _count(db, Alerta)

    res_pendientes = await db.execute(
        select(func.count()).select_from(Alerta).where(Alerta.resuelta == False)
    )
    alertas_pendientes = res_pendientes.scalar() or 0

    hoy = date.today()
    res_hoy = await db.execute(
        select(func.count()).select_from(EventoSistema).where(
            func.date(EventoSistema.timestamp) == hoy
        )
    )
    total_eventos_hoy = res_hoy.scalar() or 0

    return EstadisticasGlobales(
        total_usuarios      = total_usuarios,
        total_sistemas      = total_sistemas,
        total_servicios_web = total_servicios_web,
        total_alertas       = total_alertas,
        alertas_pendientes  = alertas_pendientes,
        total_eventos_hoy   = total_eventos_hoy,
    )


# ══════════════════════════════════════════════════════════
# Sistemas más monitorizados
# ══════════════════════════════════════════════════════════

@router.get("/sistemas-top", response_model=list[SistemaTop])
async def sistemas_top(
    limite: int = 5,
    db: AsyncSession = Depends(get_db),
    admin: Usuario = Depends(require_admin),
):
    """Devuelve los sistemas con más eventos generados."""
    result = await db.execute(
        select(
            Sistema.id.label("sistema_id"),
            Sistema.nombre,
            func.count(EventoSistema.id).label("total_eventos"),
        )
        .join(EventoSistema, EventoSistema.sistema_id == Sistema.id, isouter=True)
        .group_by(Sistema.id, Sistema.nombre)
        .order_by(func.count(EventoSistema.id).desc())
        .limit(limite)
    )
    return [
        SistemaTop(
            sistema_id    = row.sistema_id,
            nombre        = row.nombre,
            total_eventos = row.total_eventos,
        )
        for row in result.all()
    ]


# ══════════════════════════════════════════════════════════
# Reglas más utilizadas
# ══════════════════════════════════════════════════════════

@router.get("/reglas-top", response_model=list[ReglaTop])
async def reglas_top(
    limite: int = 5,
    db: AsyncSession = Depends(get_db),
    admin: Usuario = Depends(require_admin),
):
    """Devuelve las reglas que más alertas han disparado."""
    result = await db.execute(
        select(
            Regla.id.label("regla_id"),
            Regla.nombre,
            func.count(Alerta.id).label("total_alertas"),
        )
        .join(Alerta, Alerta.regla_id == Regla.id, isouter=True)
        .group_by(Regla.id, Regla.nombre)
        .order_by(func.count(Alerta.id).desc())
        .limit(limite)
    )
    return [
        ReglaTop(
            regla_id      = row.regla_id,
            nombre        = row.nombre,
            total_alertas = row.total_alertas,
        )
        for row in result.all()
    ]


# ══════════════════════════════════════════════════════════
# Gestión de usuarios (solo admin)
# ══════════════════════════════════════════════════════════

@router.get("/usuarios", response_model=list)
async def listar_todos_usuarios(
    db: AsyncSession = Depends(get_db),
    admin: Usuario = Depends(require_admin),
):
    """Lista todos los usuarios de la plataforma."""
    from app.schemas import UsuarioOut
    result = await db.execute(select(Usuario).order_by(Usuario.created_at.desc()))
    usuarios = result.scalars().all()
    return [UsuarioOut.model_validate(u) for u in usuarios]


@router.patch("/usuarios/{usuario_id}/toggle", response_model=dict)
async def toggle_usuario(
    usuario_id: str,
    db: AsyncSession = Depends(get_db),
    admin: Usuario = Depends(require_admin),
):
    """Activa o desactiva un usuario."""
    from uuid import UUID
    result = await db.execute(
        select(Usuario).where(Usuario.id == UUID(usuario_id))
    )
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if usuario.id == admin.id:
        raise HTTPException(status_code=400, detail="No puedes desactivarte a ti mismo")
    usuario.activo = not usuario.activo
    await db.commit()
    return {"id": str(usuario.id), "activo": usuario.activo}


# ══════════════════════════════════════════════════════════
# Helper
# ══════════════════════════════════════════════════════════

async def _count(db: AsyncSession, model) -> int:
    result = await db.execute(select(func.count()).select_from(model))
    return result.scalar() or 0