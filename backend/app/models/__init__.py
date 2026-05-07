import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    String, Boolean, Float, Integer, Text,
    ForeignKey, Enum, JSON
)
from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum


# ══════════════════════════════════════════════════════════
# Enums Python — espejo exacto de los tipos PostgreSQL
# ══════════════════════════════════════════════════════════

class RolUsuario(str, enum.Enum):
    admin    = "admin"
    operador = "operador"

class OperadorRegla(str, enum.Enum):
    gt  = ">"
    lt  = "<"
    gte = ">="
    lte = "<="
    eq  = "="

class SeveridadAlerta(str, enum.Enum):
    info     = "info"
    warning  = "warning"
    critical = "critical"

class TipoEvento(str, enum.Enum):
    cpu_alta      = "cpu_alta"
    ram_alta      = "ram_alta"
    disco_alto    = "disco_alto"
    http_down     = "http_down"
    http_lento    = "http_lento"
    login_fallido = "login_fallido"
    agente_caido  = "agente_caido"
    otro          = "otro"


# ══════════════════════════════════════════════════════════
# AlertaRecomendacion — clase de asociación
# No es una tabla intermedia simple: registra si el admin
# aplicó la recomendación y cuándo (atributos propios)
# ══════════════════════════════════════════════════════════

class AlertaRecomendacion(Base):
    __tablename__ = "alertas_recomendaciones"

    alerta_id        : Mapped[uuid.UUID]          = mapped_column(
        UUID(as_uuid=True), ForeignKey("alertas.id", ondelete="CASCADE"), primary_key=True
    )
    recomendacion_id : Mapped[uuid.UUID]          = mapped_column(
        UUID(as_uuid=True), ForeignKey("recomendaciones.id", ondelete="CASCADE"), primary_key=True
    )
    aplicada         : Mapped[bool]               = mapped_column(Boolean, default=False)
    aplicada_at      : Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    alerta        : Mapped["Alerta"]        = relationship(back_populates="alerta_recomendaciones")
    recomendacion : Mapped["Recomendacion"] = relationship(back_populates="alerta_recomendaciones")


# ══════════════════════════════════════════════════════════
# Usuario
# ══════════════════════════════════════════════════════════

class Usuario(Base):
    __tablename__ = "usuarios"

    id            : Mapped[uuid.UUID]   = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre        : Mapped[str]         = mapped_column(String(100), nullable=False)
    email         : Mapped[str]         = mapped_column(String(150), unique=True, nullable=False)
    password_hash : Mapped[str]         = mapped_column(String(255), nullable=False)
    rol           : Mapped[RolUsuario]  = mapped_column(
        Enum(RolUsuario, name="rol_usuario"), default=RolUsuario.operador
    )
    activo        : Mapped[bool]        = mapped_column(Boolean, default=True)
    created_at    : Mapped[datetime]    = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    sistemas      : Mapped[list["Sistema"]]     = relationship(back_populates="usuario", cascade="all, delete-orphan")
    servicios_web : Mapped[list["ServicioWeb"]] = relationship(back_populates="usuario", cascade="all, delete-orphan")
    reglas        : Mapped[list["Regla"]]       = relationship(back_populates="usuario", cascade="all, delete-orphan")


# ══════════════════════════════════════════════════════════
# Sistema
# ══════════════════════════════════════════════════════════

class Sistema(Base):
    __tablename__ = "sistemas"

    id              : Mapped[uuid.UUID]          = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id      : Mapped[uuid.UUID]          = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"))
    nombre          : Mapped[str]                = mapped_column(String(100), nullable=False)
    ip              : Mapped[Optional[str]]      = mapped_column(String(45))
    descripcion     : Mapped[Optional[str]]      = mapped_column(Text)
    activo          : Mapped[bool]               = mapped_column(Boolean, default=True)
    ultimo_contacto : Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at      : Mapped[datetime]           = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    usuario   : Mapped["Usuario"]               = relationship(back_populates="sistemas")
    snapshots : Mapped[list["MetricaSnapshot"]] = relationship(back_populates="sistema", cascade="all, delete-orphan")
    eventos   : Mapped[list["EventoSistema"]]   = relationship(back_populates="sistema")


# ══════════════════════════════════════════════════════════
# MetricaSnapshot — composición con Sistema
# ══════════════════════════════════════════════════════════

class MetricaSnapshot(Base):
    __tablename__ = "metricas_snapshot"

    id            : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sistema_id    : Mapped[uuid.UUID] = mapped_column(ForeignKey("sistemas.id", ondelete="CASCADE"))
    cpu_percent   : Mapped[float]     = mapped_column(Float, nullable=False)
    ram_percent   : Mapped[float]     = mapped_column(Float, nullable=False)
    disco_percent : Mapped[float]     = mapped_column(Float, nullable=False)
    timestamp     : Mapped[datetime]  = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    sistema : Mapped["Sistema"] = relationship(back_populates="snapshots")


# ══════════════════════════════════════════════════════════
# ServicioWeb
# ══════════════════════════════════════════════════════════

class ServicioWeb(Base):
    __tablename__ = "servicios_web"

    id          : Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id  : Mapped[uuid.UUID]  = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"))
    nombre      : Mapped[str]        = mapped_column(String(100), nullable=False)
    url         : Mapped[str]        = mapped_column(Text, nullable=False)
    intervalo_s : Mapped[int]        = mapped_column(Integer, default=60)
    activo      : Mapped[bool]       = mapped_column(Boolean, default=True)
    created_at  : Mapped[datetime]   = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    usuario : Mapped["Usuario"]          = relationship(back_populates="servicios_web")
    eventos : Mapped[list["EventoWeb"]]  = relationship(back_populates="servicio_web")


# ══════════════════════════════════════════════════════════
# Herencia de Evento — joined table inheritance
# Evento: clase abstracta con atributos comunes
# EventoSistema / EventoWeb: subclases con atributos propios
# ══════════════════════════════════════════════════════════

class Evento(Base):
    __tablename__   = "eventos"
    __mapper_args__ = {
        "polymorphic_on":       "tipo",
        "polymorphic_identity": "evento",
    }

    id        : Mapped[uuid.UUID]        = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tipo      : Mapped[TipoEvento]       = mapped_column(
        Enum(TipoEvento, name="tipo_evento",
             values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    valor     : Mapped[Optional[float]] = mapped_column(Float)
    origen    : Mapped[Optional[str]]   = mapped_column(String(100))
    metadata_ : Mapped[Optional[dict]]  = mapped_column("metadata", JSON)
    timestamp : Mapped[datetime]        = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    alertas : Mapped[list["Alerta"]] = relationship(
        back_populates="evento",
        foreign_keys="[Alerta.evento_id]",
        primaryjoin="Alerta.evento_id == Evento.id",
    )


class EventoSistema(Evento):
    """Evento originado en un servidor monitorizado."""
    __tablename__   = "eventos_sistema"
    __mapper_args__ = {"polymorphic_identity": "evento_sistema"}

    id         : Mapped[uuid.UUID]      = mapped_column(ForeignKey("eventos.id"), primary_key=True)
    sistema_id : Mapped[uuid.UUID]      = mapped_column(ForeignKey("sistemas.id", ondelete="CASCADE"))
    proceso    : Mapped[Optional[str]]  = mapped_column(String(100))
    pid        : Mapped[Optional[int]]  = mapped_column(Integer)

    sistema : Mapped["Sistema"] = relationship(back_populates="eventos")


class EventoWeb(Evento):
    """Evento originado en un servicio web monitorizado."""
    __tablename__   = "eventos_web"
    __mapper_args__ = {"polymorphic_identity": "evento_web"}

    id              : Mapped[uuid.UUID]     = mapped_column(ForeignKey("eventos.id"), primary_key=True)
    servicio_web_id : Mapped[uuid.UUID]     = mapped_column(ForeignKey("servicios_web.id", ondelete="CASCADE"))
    http_status     : Mapped[Optional[int]] = mapped_column(Integer)
    tiempo_ms       : Mapped[Optional[int]] = mapped_column(Integer)

    servicio_web : Mapped["ServicioWeb"] = relationship(back_populates="eventos")


# ══════════════════════════════════════════════════════════
# Regla
# ══════════════════════════════════════════════════════════

class Regla(Base):
    __tablename__ = "reglas"

    id         : Mapped[uuid.UUID]       = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id : Mapped[uuid.UUID]       = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"))
    nombre     : Mapped[str]             = mapped_column(String(150), nullable=False)
    metrica    : Mapped[str]             = mapped_column(String(50), nullable=False)
    operador   : Mapped[OperadorRegla]   = mapped_column(
        Enum(OperadorRegla, name="operador_regla",
             values_callable=lambda x: [e.value for e in x])
    )
    umbral     : Mapped[float]           = mapped_column(Float, nullable=False)
    severidad  : Mapped[SeveridadAlerta] = mapped_column(
        Enum(SeveridadAlerta, name="severidad_alerta"), default=SeveridadAlerta.warning
    )
    activa     : Mapped[bool]            = mapped_column(Boolean, default=True)
    created_at : Mapped[datetime]        = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    usuario : Mapped["Usuario"]      = relationship(back_populates="reglas")
    alertas : Mapped[list["Alerta"]] = relationship(back_populates="regla")


# ══════════════════════════════════════════════════════════
# Alerta
# ══════════════════════════════════════════════════════════

class Alerta(Base):
    __tablename__ = "alertas"

    id          : Mapped[uuid.UUID]          = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evento_id   : Mapped[uuid.UUID]          = mapped_column(UUID(as_uuid=True), nullable=False)
    regla_id    : Mapped[uuid.UUID]          = mapped_column(ForeignKey("reglas.id", ondelete="CASCADE"))
    severidad   : Mapped[SeveridadAlerta]    = mapped_column(
        Enum(SeveridadAlerta, name="severidad_alerta"), nullable=False
    )
    mensaje     : Mapped[str]                = mapped_column(Text, nullable=False)
    resuelta    : Mapped[bool]               = mapped_column(Boolean, default=False)
    timestamp   : Mapped[datetime]           = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    resuelta_at : Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    regla  : Mapped["Regla"]  = relationship(back_populates="alertas")
    evento : Mapped["Evento"] = relationship(
        back_populates="alertas",
        foreign_keys=[evento_id],
        primaryjoin="Alerta.evento_id == Evento.id",
    )
    alerta_recomendaciones : Mapped[list["AlertaRecomendacion"]] = relationship(back_populates="alerta")


# ══════════════════════════════════════════════════════════
# Recomendacion
# ══════════════════════════════════════════════════════════

class Recomendacion(Base):
    __tablename__ = "recomendaciones"

    id          : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tipo_alerta : Mapped[str]       = mapped_column(String(50), nullable=False)
    texto       : Mapped[str]       = mapped_column(Text, nullable=False)
    prioridad   : Mapped[int]       = mapped_column(Integer, default=1)

    alerta_recomendaciones : Mapped[list["AlertaRecomendacion"]] = relationship(back_populates="recomendacion")