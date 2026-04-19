from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.database import get_db
from app.models import ServicioWeb, Usuario
from app.schemas import ServicioWebCreate, ServicioWebUpdate, ServicioWebOut
from app.routers.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=list[ServicioWebOut])
async def listar_servicios(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    result = await db.execute(
        select(ServicioWeb).where(ServicioWeb.usuario_id == current_user.id)
    )
    return result.scalars().all()


@router.post("/", response_model=ServicioWebOut, status_code=status.HTTP_201_CREATED)
async def crear_servicio(
    datos: ServicioWebCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    servicio = ServicioWeb(**datos.model_dump(), usuario_id=current_user.id)
    db.add(servicio)
    await db.commit()
    await db.refresh(servicio)
    return servicio


@router.patch("/{servicio_id}", response_model=ServicioWebOut)
async def actualizar_servicio(
    servicio_id: UUID,
    datos: ServicioWebUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    servicio = await _get_or_404(db, servicio_id, current_user.id)
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(servicio, campo, valor)
    await db.commit()
    await db.refresh(servicio)
    return servicio


@router.delete("/{servicio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_servicio(
    servicio_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    servicio = await _get_or_404(db, servicio_id, current_user.id)
    await db.delete(servicio)
    await db.commit()


async def _get_or_404(db, servicio_id, usuario_id):
    result = await db.execute(
        select(ServicioWeb).where(
            ServicioWeb.id == servicio_id,
            ServicioWeb.usuario_id == usuario_id,
        )
    )
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Servicio web no encontrado")
    return s
