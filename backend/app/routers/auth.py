from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Usuario
from app.core.security import verify_password, create_access_token, decode_token
from pydantic import BaseModel
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter()
security = HTTPBearer()


class Token(BaseModel):
    access_token: str
    token_type: str


@router.post("/login", response_model=Token)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Usuario).where(Usuario.email == form.username))
    usuario = result.scalar_one_or_none()

    if not usuario or not verify_password(form.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token({"sub": str(usuario.id), "rol": usuario.rol})
    return {"access_token": token, "token_type": "bearer"}


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Usuario:
    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    result = await db.execute(select(Usuario).where(Usuario.id == payload["sub"]))
    usuario = result.scalar_one_or_none()
    if not usuario or not usuario.activo:
        raise HTTPException(status_code=401, detail="Usuario no encontrado o inactivo")
    return usuario
