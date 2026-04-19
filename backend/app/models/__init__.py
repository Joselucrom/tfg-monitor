import uuid
from datetime import datetime
from sqlalchemy import func
from sqlalchemy import String, Boolean, Float, Integer, Text, ForeignKey, Enum, CheckConstraint, Table, Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum

# ── Tabla intermedia (many-to-many) ──────────────────────
alertas_recomendaciones = Table(
    "alertas_recomendaciones",
    Base.metadata,
    Column("alerta_id",        UUID(as_uuid=True), ForeignKey("alertas.id", ondelete="CASCADE"), primary_key=True),
    Column("recomendacion_id", UUID(as_uuid=True), ForeignKey("recomendaciones.id", ondelete="CASCADE"), primary_key=True),
)


# ── Enums Python (espejo de los enums PostgreSQL) ────────

class RolUsuario(str, enum.Enum):
    admin = "admin"
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


# ── Modelos ──────────────────────────────────────────────

class Usuario(Base):
    __tablename__ = "usuarios"

    id            : Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre        : Mapped[str]        = mapped_column(String(100), nullable=False)
    email         : Mapped[str]        = mapped_column(String(150), unique=True, nullable=False)
    password_hash : Mapped[str]        = mapped_column(String(255), nullable=False)
    rol           : Mapped[RolUsuario] = mapped_column(Enum(RolUsuario), default=RolUsuario.operador)
    activo        : Mapped[bool]       = mapped_column(Boolean, default=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())

    sistemas      : Mapped[list["Sistema"]]      = relationship(back_populates="usuario")
    servicios_web : Mapped[list["ServicioWeb"]]  = relationship(back_populates="usuario")
    reglas        : Mapped[list["Regla"]]        = relationship(back_populates="usuario")


class Sistema(Base):
    __tablename__ = "sistemas"

    id              : Mapped[uuid.UUID]        = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id      : Mapped[uuid.UUID]        = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"))
    nombre          : Mapped[str]              = mapped_column(String(100), nullable=False)
    ip              : Mapped[str | None]       = mapped_column(String(45))
    descripcion     : Mapped[str | None]       = mapped_column(Text)
    activo          : Mapped[bool]             = mapped_column(Boolean, default=True)
    ultimo_contacto = mapped_column(DateTime(timezone=True))
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())

    usuario : Mapped["Usuario"]        = relationship(back_populates="sistemas")
    eventos : Mapped[list["Evento"]]   = relationship(back_populates="sistema")


class ServicioWeb(Base):
    __tablename__ = "servicios_web"

    id           : Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id   : Mapped[uuid.UUID]  = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"))
    nombre       : Mapped[str]        = mapped_column(String(100), nullable=False)
    url          : Mapped[str]        = mapped_column(Text, nullable=False)
    intervalo_s  : Mapped[int]        = mapped_column(Integer, default=60)
    activo       : Mapped[bool]       = mapped_column(Boolean, default=True)
    created_at   : Mapped[datetime]   = mapped_column(DateTime(timezone=True), server_default=func.now())

    usuario : Mapped["Usuario"]       = relationship(back_populates="servicios_web")
    eventos : Mapped[list["Evento"]]  = relationship(back_populates="servicio_web")


class Regla(Base):
    __tablename__ = "reglas"

    id         : Mapped[uuid.UUID]        = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id : Mapped[uuid.UUID]        = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"))
    nombre     : Mapped[str]              = mapped_column(String(150), nullable=False)
    metrica    : Mapped[str]              = mapped_column(String(50), nullable=False)
    operador   : Mapped[OperadorRegla]    = mapped_column(Enum(OperadorRegla))
    umbral     : Mapped[float]            = mapped_column(Float, nullable=False)
    severidad  : Mapped[SeveridadAlerta]  = mapped_column(Enum(SeveridadAlerta), default=SeveridadAlerta.warning)
    activa     : Mapped[bool]             = mapped_column(Boolean, default=True)
    created_at : Mapped[datetime]         = mapped_column(DateTime(timezone=True), server_default=func.now())

    usuario : Mapped["Usuario"]       = relationship(back_populates="reglas")
    alertas : Mapped[list["Alerta"]]  = relationship(back_populates="regla")


class Evento(Base):
    __tablename__ = "eventos"
    __table_args__ = (
        CheckConstraint(
            "(sistema_id IS NOT NULL AND servicio_web_id IS NULL) OR "
            "(sistema_id IS NULL AND servicio_web_id IS NOT NULL)",
            name="evento_origen_check"
        ),
    )

    id              : Mapped[uuid.UUID]       = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sistema_id      : Mapped[uuid.UUID | None] = mapped_column(ForeignKey("sistemas.id", ondelete="SET NULL"))
    servicio_web_id : Mapped[uuid.UUID | None] = mapped_column(ForeignKey("servicios_web.id", ondelete="SET NULL"))
    tipo            : Mapped[TipoEvento]       = mapped_column(Enum(TipoEvento), nullable=False)
    valor           : Mapped[float | None]     = mapped_column(Float)
    origen          : Mapped[str | None]       = mapped_column(String(100))
    timestamp = mapped_column(DateTime(timezone=True), server_default=func.now())

    sistema      : Mapped["Sistema | None"]      = relationship(back_populates="eventos")
    servicio_web : Mapped["ServicioWeb | None"]  = relationship(back_populates="eventos")
    alertas      : Mapped[list["Alerta"]]        = relationship(back_populates="evento")


class Alerta(Base):
    __tablename__ = "alertas"

    id          : Mapped[uuid.UUID]        = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evento_id   : Mapped[uuid.UUID]        = mapped_column(ForeignKey("eventos.id", ondelete="CASCADE"))
    regla_id    : Mapped[uuid.UUID]        = mapped_column(ForeignKey("reglas.id", ondelete="CASCADE"))
    severidad   : Mapped[SeveridadAlerta]  = mapped_column(Enum(SeveridadAlerta), nullable=False)
    mensaje     : Mapped[str]              = mapped_column(Text, nullable=False)
    resuelta    : Mapped[bool]             = mapped_column(Boolean, default=False)
    timestamp = mapped_column(DateTime(timezone=True), server_default=func.now())
    resuelta_at = mapped_column(DateTime(timezone=True))

    evento : Mapped["Evento"]  = relationship(back_populates="alertas")
    regla  : Mapped["Regla"]   = relationship(back_populates="alertas")


class Recomendacion(Base):
    __tablename__ = "recomendaciones"

    id          : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tipo_alerta : Mapped[str]       = mapped_column(String(50), nullable=False)
    texto       : Mapped[str]       = mapped_column(Text, nullable=False)
    prioridad   : Mapped[int]       = mapped_column(Integer, default=1)
