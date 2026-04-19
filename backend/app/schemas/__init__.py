"""
Schemas Pydantic — validación de entrada/salida de la API.
Separados de los modelos SQLAlchemy para mantener la arquitectura limpia.
"""
from pydantic import BaseModel, EmailStr, HttpUrl, field_validator
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.models import RolUsuario, OperadorRegla, SeveridadAlerta, TipoEvento


# ── Utilidad base ─────────────────────────────────────────

class BaseSchema(BaseModel):
    model_config = {"from_attributes": True}


# ── Usuario ───────────────────────────────────────────────

class UsuarioCreate(BaseModel):
    nombre: str
    email: EmailStr
    password: str
    rol: RolUsuario = RolUsuario.operador


class UsuarioOut(BaseSchema):
    id: UUID
    nombre: str
    email: str
    rol: RolUsuario
    activo: bool
    created_at: datetime


# ── Sistema ───────────────────────────────────────────────

class SistemaCreate(BaseModel):
    nombre: str
    ip: Optional[str] = None
    descripcion: Optional[str] = None


class SistemaUpdate(BaseModel):
    nombre: Optional[str] = None
    ip: Optional[str] = None
    descripcion: Optional[str] = None
    activo: Optional[bool] = None


class SistemaOut(BaseSchema):
    id: UUID
    nombre: str
    ip: Optional[str]
    descripcion: Optional[str]
    activo: bool
    ultimo_contacto: Optional[datetime]
    created_at: datetime


# ── ServicioWeb ───────────────────────────────────────────

class ServicioWebCreate(BaseModel):
    nombre: str
    url: str
    intervalo_s: int = 60

    @field_validator("intervalo_s")
    @classmethod
    def intervalo_minimo(cls, v: int) -> int:
        if v < 10:
            raise ValueError("El intervalo mínimo es 10 segundos")
        return v


class ServicioWebUpdate(BaseModel):
    nombre: Optional[str] = None
    url: Optional[str] = None
    intervalo_s: Optional[int] = None
    activo: Optional[bool] = None


class ServicioWebOut(BaseSchema):
    id: UUID
    nombre: str
    url: str
    intervalo_s: int
    activo: bool
    created_at: datetime


# ── Regla ─────────────────────────────────────────────────

class ReglaCreate(BaseModel):
    nombre: str
    metrica: str
    operador: OperadorRegla
    umbral: float
    severidad: SeveridadAlerta = SeveridadAlerta.warning


class ReglaOut(BaseSchema):
    id: UUID
    nombre: str
    metrica: str
    operador: OperadorRegla
    umbral: float
    severidad: SeveridadAlerta
    activa: bool
    created_at: datetime


# ── Evento ────────────────────────────────────────────────

class EventoCreate(BaseModel):
    sistema_id: Optional[UUID] = None
    servicio_web_id: Optional[UUID] = None
    tipo: TipoEvento
    valor: Optional[float] = None
    origen: Optional[str] = None

    @field_validator("servicio_web_id")
    @classmethod
    def validar_origen_exclusivo(cls, v, info):
        if v is not None and info.data.get("sistema_id") is not None:
            raise ValueError("Un evento no puede tener sistema_id y servicio_web_id a la vez")
        return v


class EventoOut(BaseSchema):
    id: UUID
    sistema_id: Optional[UUID]
    servicio_web_id: Optional[UUID]
    tipo: TipoEvento
    valor: Optional[float]
    origen: Optional[str]
    timestamp: datetime


# ── Alerta ────────────────────────────────────────────────

class AlertaOut(BaseSchema):
    id: UUID
    evento_id: UUID
    regla_id: UUID
    severidad: SeveridadAlerta
    mensaje: str
    resuelta: bool
    timestamp: datetime
    resuelta_at: Optional[datetime]


# ── Recomendación ─────────────────────────────────────────

class RecomendacionOut(BaseSchema):
    id: UUID
    tipo_alerta: str
    texto: str
    prioridad: int


# ── Auth ──────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: UUID
    rol: RolUsuario
