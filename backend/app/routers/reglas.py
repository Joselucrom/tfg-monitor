from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.database import get_db
from app.models import Regla, Usuario
from app.schemas import ReglaCreate, ReglaOut
from app.routers.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=list[ReglaOut])
async def listar_reglas(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    result = await db.execute(
        select(Regla).where(Regla.usuario_id == current_user.id)
    )
    return result.scalars().all()


@router.post("/", response_model=ReglaOut, status_code=status.HTTP_201_CREATED)
async def crear_regla(
    datos: ReglaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    regla = Regla(**datos.model_dump(), usuario_id=current_user.id)
    db.add(regla)
    await db.commit()
    await db.refresh(regla)
    return regla


@router.patch("/{regla_id}/toggle", response_model=ReglaOut)
async def toggle_regla(
    regla_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Activa o desactiva una regla."""
    result = await db.execute(
        select(Regla).where(Regla.id == regla_id, Regla.usuario_id == current_user.id)
    )
    regla = result.scalar_one_or_none()
    if not regla:
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    regla.activa = not regla.activa
    await db.commit()
    await db.refresh(regla)
    return regla


@router.delete("/{regla_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_regla(
    regla_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    result = await db.execute(
        select(Regla).where(Regla.id == regla_id, Regla.usuario_id == current_user.id)
    )
    regla = result.scalar_one_or_none()
    if not regla:
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    await db.delete(regla)
    await db.commit()
