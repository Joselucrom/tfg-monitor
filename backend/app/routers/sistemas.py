from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime

from app.database import get_db
from app.models import Sistema, Usuario
from app.schemas import SistemaCreate, SistemaUpdate, SistemaOut
from app.routers.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=list[SistemaOut])
async def listar_sistemas(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Devuelve todos los sistemas del usuario autenticado."""
    result = await db.execute(
        select(Sistema).where(Sistema.usuario_id == current_user.id)
    )
    return result.scalars().all()


@router.get("/{sistema_id}", response_model=SistemaOut)
async def obtener_sistema(
    sistema_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await _get_or_404(db, sistema_id, current_user.id)


@router.post("/", response_model=SistemaOut, status_code=status.HTTP_201_CREATED)
async def crear_sistema(
    datos: SistemaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    sistema = Sistema(**datos.model_dump(), usuario_id=current_user.id)
    db.add(sistema)
    await db.commit()
    await db.refresh(sistema)
    return sistema


@router.patch("/{sistema_id}", response_model=SistemaOut)
async def actualizar_sistema(
    sistema_id: UUID,
    datos: SistemaUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    sistema = await _get_or_404(db, sistema_id, current_user.id)
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(sistema, campo, valor)
    await db.commit()
    await db.refresh(sistema)
    return sistema


@router.delete("/{sistema_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_sistema(
    sistema_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    sistema = await _get_or_404(db, sistema_id, current_user.id)
    await db.delete(sistema)
    await db.commit()


@router.post("/{sistema_id}/ping", response_model=SistemaOut)
async def ping_sistema(
    sistema_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """El agente llama a este endpoint para actualizar ultimo_contacto."""
    sistema = await _get_or_404(db, sistema_id, current_user.id)
    sistema.ultimo_contacto = datetime.utcnow()
    await db.commit()
    await db.refresh(sistema)
    return sistema


async def _get_or_404(db: AsyncSession, sistema_id: UUID, usuario_id: UUID) -> Sistema:
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
