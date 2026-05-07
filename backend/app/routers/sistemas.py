from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from uuid import UUID
from datetime import datetime

from app.database import get_db
from app.models import Sistema, Usuario
from app.schemas import SistemaCreate, SistemaUpdate, SistemaOut
from app.routers.auth import get_current_user

router = APIRouter()


# ══════════════════════════════════════════════════════════
# Listar y buscar
# ══════════════════════════════════════════════════════════

@router.get("/", response_model=list[SistemaOut])
async def listar_sistemas(
    activo: bool | None = Query(None, description="Filtra por sistemas activos o inactivos"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Devuelve todos los sistemas del usuario autenticado."""
    q = select(Sistema).where(Sistema.usuario_id == current_user.id)
    if activo is not None:
        q = q.where(Sistema.activo == activo)
    q = q.order_by(Sistema.created_at.desc())
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/buscar", response_model=SistemaOut)
async def buscar_sistema(
    ip: str | None = Query(None, description="IP del sistema"),
    nombre: str | None = Query(None, description="Nombre del sistema"),
    db: AsyncSession = Depends(get_db),
):
    """
    El agente usa este endpoint para obtener el UUID
    de un sistema a partir de su IP o nombre.
    No requiere JWT.
    """
    if not ip and not nombre:
        raise HTTPException(
            status_code=400,
            detail="Debes indicar al menos ip o nombre"
        )

    conditions = []
    if ip:
        conditions.append(Sistema.ip == ip)
    if nombre:
        conditions.append(Sistema.nombre == nombre)

    result = await db.execute(
        select(Sistema).where(
            or_(*conditions),
            Sistema.activo == True,
        )
    )
    sistema = result.scalar_one_or_none()
    if not sistema:
        raise HTTPException(status_code=404, detail="Sistema no encontrado")
    return sistema


@router.get("/{sistema_id}", response_model=SistemaOut)
async def obtener_sistema(
    sistema_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Devuelve el detalle de un sistema."""
    return await _get_or_404(db, sistema_id, current_user.id)


# ══════════════════════════════════════════════════════════
# Crear
# ══════════════════════════════════════════════════════════

@router.post("/", response_model=SistemaOut, status_code=status.HTTP_201_CREATED)
async def crear_sistema(
    datos: SistemaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Registra un nuevo sistema para monitorizar."""
    sistema = Sistema(**datos.model_dump(), usuario_id=current_user.id)
    db.add(sistema)
    await db.commit()
    await db.refresh(sistema)
    return sistema


# ══════════════════════════════════════════════════════════
# Editar
# ══════════════════════════════════════════════════════════

@router.patch("/{sistema_id}", response_model=SistemaOut)
async def actualizar_sistema(
    sistema_id: UUID,
    datos: SistemaUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Actualiza los campos de un sistema (PATCH parcial)."""
    sistema = await _get_or_404(db, sistema_id, current_user.id)
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(sistema, campo, valor)
    await db.commit()
    await db.refresh(sistema)
    return sistema


# ══════════════════════════════════════════════════════════
# Eliminar
# ══════════════════════════════════════════════════════════

@router.delete("/{sistema_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_sistema(
    sistema_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Elimina un sistema y todos sus datos asociados
    (snapshots y eventos por CASCADE en BD).
    """
    sistema = await _get_or_404(db, sistema_id, current_user.id)
    await db.delete(sistema)
    await db.commit()


# ══════════════════════════════════════════════════════════
# Ping — el agente actualiza ultimo_contacto
# ══════════════════════════════════════════════════════════

@router.post("/{sistema_id}/ping", response_model=SistemaOut)
async def ping_sistema(
    sistema_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    El agente llama a este endpoint en cada ciclo
    para actualizar ultimo_contacto.
    No requiere JWT.
    """
    result = await db.execute(
        select(Sistema).where(Sistema.id == sistema_id)
    )
    sistema = result.scalar_one_or_none()
    if not sistema:
        raise HTTPException(status_code=404, detail="Sistema no encontrado")
    sistema.ultimo_contacto = datetime.utcnow()
    await db.commit()
    await db.refresh(sistema)
    return sistema


# ══════════════════════════════════════════════════════════
# Helper
# ══════════════════════════════════════════════════════════

async def _get_or_404(
    db: AsyncSession, sistema_id: UUID, usuario_id: UUID
) -> Sistema:
    result = await db.execute(
        select(Sistema).where(
            Sistema.id == sistema_id,
            Sistema.usuario_id == usuario_id,
        )
    )
    sistema = result.scalar_one_or_none()
    if not sistema:
        raise HTTPException(status_code=404, detail="Sistema no encontrado")
    return sistema