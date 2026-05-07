from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.database import get_db
from app.models import Regla, Usuario
from app.schemas import ReglaCreate, ReglaUpdate, ReglaOut
from app.routers.auth import get_current_user

router = APIRouter()


# ══════════════════════════════════════════════════════════
# Listar y obtener
# ══════════════════════════════════════════════════════════

@router.get("/", response_model=list[ReglaOut])
async def listar_reglas(
    activa: bool | None = Query(None, description="Filtra por reglas activas o inactivas"),
    metrica: str | None = Query(None, description="Filtra por tipo de métrica"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Lista las reglas del usuario autenticado con filtros opcionales."""
    q = select(Regla).where(Regla.usuario_id == current_user.id)
    if activa is not None:
        q = q.where(Regla.activa == activa)
    if metrica:
        q = q.where(Regla.metrica == metrica)
    q = q.order_by(Regla.created_at.desc())
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{regla_id}", response_model=ReglaOut)
async def obtener_regla(
    regla_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Devuelve el detalle de una regla."""
    return await _get_or_404(db, regla_id, current_user.id)


# ══════════════════════════════════════════════════════════
# Crear
# ══════════════════════════════════════════════════════════

@router.post("/", response_model=ReglaOut, status_code=status.HTTP_201_CREATED)
async def crear_regla(
    datos: ReglaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Crea una nueva regla de alerta."""
    regla = Regla(**datos.model_dump(), usuario_id=current_user.id)
    db.add(regla)
    await db.commit()
    await db.refresh(regla)
    return regla


# ══════════════════════════════════════════════════════════
# Editar
# ══════════════════════════════════════════════════════════

@router.patch("/{regla_id}", response_model=ReglaOut)
async def editar_regla(
    regla_id: UUID,
    datos: ReglaUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Edita los campos de una regla existente.
    Solo se actualizan los campos enviados (PATCH parcial).
    """
    regla = await _get_or_404(db, regla_id, current_user.id)
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(regla, campo, valor)
    await db.commit()
    await db.refresh(regla)
    return regla


@router.patch("/{regla_id}/toggle", response_model=ReglaOut)
async def toggle_regla(
    regla_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Activa o desactiva una regla sin modificar el resto de campos."""
    regla = await _get_or_404(db, regla_id, current_user.id)
    regla.activa = not regla.activa
    await db.commit()
    await db.refresh(regla)
    return regla


# ══════════════════════════════════════════════════════════
# Eliminar
# ══════════════════════════════════════════════════════════

@router.delete("/{regla_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_regla(
    regla_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Elimina una regla permanentemente."""
    regla = await _get_or_404(db, regla_id, current_user.id)
    await db.delete(regla)
    await db.commit()


# ══════════════════════════════════════════════════════════
# Helper
# ══════════════════════════════════════════════════════════

async def _get_or_404(db: AsyncSession, regla_id: UUID, usuario_id: UUID) -> Regla:
    result = await db.execute(
        select(Regla).where(
            Regla.id == regla_id,
            Regla.usuario_id == usuario_id,
        )
    )
    regla = result.scalar_one_or_none()
    if not regla:
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    return regla