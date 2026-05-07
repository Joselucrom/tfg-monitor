from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Usuario, RolUsuario
from app.schemas import UsuarioCreate, UsuarioOut
from app.core.security import hash_password
from app.routers.auth import get_current_user
from pydantic import BaseModel

router = APIRouter()


# ══════════════════════════════════════════════════════════
# Schema local — cambio de contraseña
# ══════════════════════════════════════════════════════════

class CambioPassword(BaseModel):
    password_actual: str
    password_nuevo:  str


# ══════════════════════════════════════════════════════════
# Registro
# ══════════════════════════════════════════════════════════

@router.post("/", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
async def registrar_usuario(
    datos: UsuarioCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Registro de nuevo usuario.
    El rol 'admin' solo puede asignarse si no existe ningún admin aún
    (primer usuario del sistema). A partir de ahí, los nuevos admins
    los crea un admin existente desde el panel de administración.
    """
    # Verificar email único
    result = await db.execute(
        select(Usuario).where(Usuario.email == datos.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="El email ya está registrado"
        )

    # Protección: si piden rol admin, verificar que no existe ninguno aún
    if datos.rol == RolUsuario.admin:
        result_admin = await db.execute(
            select(Usuario).where(Usuario.rol == RolUsuario.admin).limit(1)
        )
        if result_admin.scalar_one_or_none():
            raise HTTPException(
                status_code=403,
                detail="Ya existe un administrador. Contacta con el admin para crear tu cuenta."
            )

    usuario = Usuario(
        nombre        = datos.nombre,
        email         = datos.email,
        password_hash = hash_password(datos.password),
        rol           = datos.rol,
    )
    db.add(usuario)
    await db.commit()
    await db.refresh(usuario)
    return usuario


# ══════════════════════════════════════════════════════════
# Perfil del usuario autenticado
# ══════════════════════════════════════════════════════════

@router.get("/me", response_model=UsuarioOut)
async def perfil(
    current_user: Usuario = Depends(get_current_user),
):
    """Devuelve los datos del usuario autenticado."""
    return current_user


@router.patch("/me", response_model=UsuarioOut)
async def actualizar_perfil(
    datos: dict,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Permite al usuario actualizar su nombre.
    El email y el rol no se pueden cambiar desde aquí.
    """
    if "nombre" in datos:
        current_user.nombre = datos["nombre"]
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def cambiar_password(
    datos: CambioPassword,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Permite al usuario cambiar su contraseña.
    Requiere la contraseña actual para verificar identidad.
    """
    from app.core.security import verify_password
    if not verify_password(datos.password_actual, current_user.password_hash):
        raise HTTPException(
            status_code=400,
            detail="La contraseña actual no es correcta"
        )
    current_user.password_hash = hash_password(datos.password_nuevo)
    await db.commit()