"""
Schemas Pydantic v2 — validación de entrada/salida de la API.
Separados de los modelos SQLAlchemy para mantener la arquitectura limpia.
Refleja la herencia de Evento y la clase de asociación AlertaRecomendacion.
"""
from pydantic import BaseModel, EmailStr, field_validator, model_validator
from typing import Optional, Any
from datetime import datetime
from uuid import UUID
from app.models import RolUsuario, OperadorRegla, SeveridadAlerta, TipoEvento


# ══════════════════════════════════════════════════════════
# Base
# ══════════════════════════════════════════════════════════

class BaseSchema(BaseModel):
    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════
# Usuario
# ══════════════════════════════════════════════════════════

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


# ══════════════════════════════════════════════════════════
# Sistema
# ══════════════════════════════════════════════════════════

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


# ══════════════════════════════════════════════════════════
# MetricaSnapshot
# ══════════════════════════════════════════════════════════

class MetricaSnapshotCreate(BaseModel):
    """El agente envía este payload al registrar métricas."""
    sistema_id:    UUID
    cpu_percent:   float
    ram_percent:   float
    disco_percent: float

    @field_validator("cpu_percent", "ram_percent", "disco_percent")
    @classmethod
    def porcentaje_valido(cls, v: float) -> float:
        if not 0.0 <= v <= 100.0:
            raise ValueError("El porcentaje debe estar entre 0 y 100")
        return v


class MetricaSnapshotOut(BaseSchema):
    id:            UUID
    sistema_id:    UUID
    cpu_percent:   float
    ram_percent:   float
    disco_percent: float
    timestamp:     datetime


# ══════════════════════════════════════════════════════════
# ServicioWeb
# ══════════════════════════════════════════════════════════

class ServicioWebCreate(BaseModel):
    nombre:      str
    url:         str
    intervalo_s: int = 60

    @field_validator("intervalo_s")
    @classmethod
    def intervalo_minimo(cls, v: int) -> int:
        if v < 10:
            raise ValueError("El intervalo mínimo es 10 segundos")
        return v


class ServicioWebUpdate(BaseModel):
    nombre:      Optional[str]  = None
    url:         Optional[str]  = None
    intervalo_s: Optional[int]  = None
    activo:      Optional[bool] = None


class ServicioWebOut(BaseSchema):
    id:          UUID
    nombre:      str
    url:         str
    intervalo_s: int
    activo:      bool
    created_at:  datetime


# ══════════════════════════════════════════════════════════
# Regla
# ══════════════════════════════════════════════════════════

class ReglaCreate(BaseModel):
    nombre:    str
    metrica:   str
    operador:  OperadorRegla
    umbral:    float
    severidad: SeveridadAlerta = SeveridadAlerta.warning


class ReglaUpdate(BaseModel):
    nombre:    Optional[str]            = None
    metrica:   Optional[str]            = None
    operador:  Optional[OperadorRegla]  = None
    umbral:    Optional[float]          = None
    severidad: Optional[SeveridadAlerta] = None
    activa:    Optional[bool]           = None


class ReglaOut(BaseSchema):
    id:        UUID
    nombre:    str
    metrica:   str
    operador:  OperadorRegla
    umbral:    float
    severidad: SeveridadAlerta
    activa:    bool
    created_at: datetime


# ══════════════════════════════════════════════════════════
# Eventos — herencia reflejada en schemas
# ══════════════════════════════════════════════════════════

class EventoSistemaCreate(BaseModel):
    """Payload que envía el agente para eventos de servidor."""
    sistema_id: UUID
    tipo:       TipoEvento
    valor:      Optional[float]      = None
    origen:     Optional[str]        = None
    metadata:   Optional[dict]       = None
    proceso:    Optional[str]        = None
    pid:        Optional[int]        = None

    @field_validator("tipo")
    @classmethod
    def tipo_valido_sistema(cls, v: TipoEvento) -> TipoEvento:
        tipos_sistema = {
            TipoEvento.cpu_alta,
            TipoEvento.ram_alta,
            TipoEvento.disco_alto,
            TipoEvento.login_fallido,
            TipoEvento.agente_caido,
            TipoEvento.otro,
        }
        if v not in tipos_sistema:
            raise ValueError(f"Tipo '{v}' no es válido para EventoSistema")
        return v


class EventoWebCreate(BaseModel):
    """Payload para eventos de servicios web monitorizados."""
    servicio_web_id: UUID
    tipo:            TipoEvento
    valor:           Optional[float] = None
    origen:          Optional[str]   = None
    metadata:        Optional[dict]  = None
    http_status:     Optional[int]   = None
    tiempo_ms:       Optional[int]   = None

    @field_validator("tipo")
    @classmethod
    def tipo_valido_web(cls, v: TipoEvento) -> TipoEvento:
        tipos_web = {TipoEvento.http_down, TipoEvento.http_lento, TipoEvento.otro}
        if v not in tipos_web:
            raise ValueError(f"Tipo '{v}' no es válido para EventoWeb")
        return v


class EventoSistemaOut(BaseSchema):
    id:         UUID
    sistema_id: UUID
    tipo:       TipoEvento
    valor:      Optional[float]
    origen:     Optional[str]
    proceso:    Optional[str]
    pid:        Optional[int]
    timestamp:  datetime


class EventoWebOut(BaseSchema):
    id:              UUID
    servicio_web_id: UUID
    tipo:            TipoEvento
    valor:           Optional[float]
    origen:          Optional[str]
    http_status:     Optional[int]
    tiempo_ms:       Optional[int]
    timestamp:       datetime


# ══════════════════════════════════════════════════════════
# AlertaRecomendacion — clase de asociación con atributos
# ══════════════════════════════════════════════════════════

class AlertaRecomendacionOut(BaseSchema):
    alerta_id:        UUID
    recomendacion_id: UUID
    aplicada:         bool
    aplicada_at:      Optional[datetime]
    texto:            Optional[str] = None
    tipo_alerta:      Optional[str] = None
    prioridad:        Optional[int] = None


class AlertaRecomendacionUpdate(BaseModel):
    """Para marcar una recomendación como aplicada."""
    aplicada: bool


# ══════════════════════════════════════════════════════════
# Alerta
# ══════════════════════════════════════════════════════════

class AlertaOut(BaseSchema):
    id:          UUID
    evento_id:   UUID
    regla_id:    UUID
    severidad:   SeveridadAlerta
    mensaje:     str
    resuelta:    bool
    timestamp:   datetime
    resuelta_at: Optional[datetime]


# ══════════════════════════════════════════════════════════
# Recomendacion
# ══════════════════════════════════════════════════════════

class RecomendacionOut(BaseSchema):
    id:          UUID
    tipo_alerta: str
    texto:       str
    prioridad:   int


# ══════════════════════════════════════════════════════════
# Admin — schemas para endpoints exclusivos del admin
# ══════════════════════════════════════════════════════════

class EstadisticasGlobales(BaseSchema):
    """Resumen global de uso de la plataforma."""
    total_usuarios:      int
    total_sistemas:      int
    total_servicios_web: int
    total_alertas:       int
    alertas_pendientes:  int
    total_eventos_hoy:   int


class SistemaTop(BaseSchema):
    """Sistema con más eventos generados."""
    sistema_id:   UUID
    nombre:       str
    total_eventos: int


class ReglaTop(BaseSchema):
    """Regla que más alertas ha disparado."""
    regla_id:      UUID
    nombre:        str
    total_alertas: int


# ══════════════════════════════════════════════════════════
# Auth
# ══════════════════════════════════════════════════════════

class Token(BaseModel):
    access_token: str
    token_type:   str


class TokenData(BaseModel):
    user_id: UUID
    rol:     RolUsuario