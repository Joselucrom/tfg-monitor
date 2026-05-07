-- ============================================================
-- Plataforma de Monitorización y Seguridad — TFG UCA
-- Diseño físico de datos v2 — PostgreSQL
-- Refleja el modelo de clases con herencia, composición,
-- agregación y clase de asociación
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── Tipos enumerados ──────────────────────────────────────

CREATE TYPE rol_usuario AS ENUM ('admin', 'operador');

CREATE TYPE operador_regla AS ENUM ('>', '<', '>=', '<=', '=');

CREATE TYPE severidad_alerta AS ENUM ('info', 'warning', 'critical');

CREATE TYPE tipo_evento AS ENUM (
    'cpu_alta',
    'ram_alta',
    'disco_alto',
    'http_down',
    'http_lento',
    'login_fallido',
    'agente_caido',
    'otro'
);

-- ── Tabla: usuarios ───────────────────────────────────────

CREATE TABLE usuarios (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre        VARCHAR(100)     NOT NULL,
    email         VARCHAR(150)     NOT NULL UNIQUE,
    password_hash VARCHAR(255)     NOT NULL,
    rol           rol_usuario      NOT NULL DEFAULT 'operador',
    activo        BOOLEAN          NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ      NOT NULL DEFAULT NOW()
);

-- ── Tabla: sistemas ───────────────────────────────────────

CREATE TABLE sistemas (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id       UUID         NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    nombre           VARCHAR(100) NOT NULL,
    ip               VARCHAR(45),
    descripcion      TEXT,
    activo           BOOLEAN      NOT NULL DEFAULT TRUE,
    ultimo_contacto  TIMESTAMPTZ,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ── Tabla: metricas_snapshot ──────────────────────────────
-- Composición con sistemas: si se elimina el sistema,
-- sus snapshots desaparecen (ON DELETE CASCADE)

CREATE TABLE metricas_snapshot (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sistema_id      UUID        NOT NULL REFERENCES sistemas(id) ON DELETE CASCADE,
    cpu_percent     FLOAT       NOT NULL,
    ram_percent     FLOAT       NOT NULL,
    disco_percent   FLOAT       NOT NULL,
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Tabla: servicios_web ──────────────────────────────────

CREATE TABLE servicios_web (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id   UUID         NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    nombre       VARCHAR(100) NOT NULL,
    url          TEXT         NOT NULL,
    intervalo_s  INT          NOT NULL DEFAULT 60,
    activo       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ── Tabla: reglas ─────────────────────────────────────────

CREATE TABLE reglas (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id   UUID             NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    nombre       VARCHAR(150)     NOT NULL,
    metrica      VARCHAR(50)      NOT NULL,
    operador     operador_regla   NOT NULL,
    umbral       FLOAT            NOT NULL,
    severidad    severidad_alerta NOT NULL DEFAULT 'warning',
    activa       BOOLEAN          NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMPTZ      NOT NULL DEFAULT NOW()
);

-- ── Herencia de eventos ───────────────────────────────────
-- Patrón tabla padre + tablas hijas (herencia PostgreSQL)
-- La tabla padre recoge los atributos comunes.
-- Cada subclase añade sus atributos específicos.

CREATE TABLE eventos (
    id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tipo      tipo_evento NOT NULL,
    valor     FLOAT,
    origen    VARCHAR(100),
    metadata  JSONB,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Subclase: EventoSistema
-- Atributos específicos de eventos originados en servidores

CREATE TABLE eventos_sistema (
    sistema_id  UUID NOT NULL REFERENCES sistemas(id) ON DELETE CASCADE,
    proceso     VARCHAR(100),
    pid         INT
) INHERITS (eventos);

ALTER TABLE eventos_sistema
    ADD CONSTRAINT pk_eventos_sistema PRIMARY KEY (id);

-- Subclase: EventoWeb
-- Atributos específicos de eventos originados en servicios web

CREATE TABLE eventos_web (
    servicio_web_id  UUID NOT NULL REFERENCES servicios_web(id) ON DELETE CASCADE,
    http_status      INT,
    tiempo_ms        INT
) INHERITS (eventos);

ALTER TABLE eventos_web
    ADD CONSTRAINT pk_eventos_web PRIMARY KEY (id);

-- ── Tabla: alertas ────────────────────────────────────────
-- evento_id puede referenciar eventos_sistema o eventos_web
-- Se usa UUID sin FK directa por la herencia de tablas

CREATE TABLE alertas (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evento_id   UUID             NOT NULL,
    regla_id    UUID             NOT NULL REFERENCES reglas(id) ON DELETE CASCADE,
    severidad   severidad_alerta NOT NULL,
    mensaje     TEXT             NOT NULL,
    resuelta    BOOLEAN          NOT NULL DEFAULT FALSE,
    timestamp   TIMESTAMPTZ      NOT NULL DEFAULT NOW(),
    resuelta_at TIMESTAMPTZ
);

-- ── Tabla: recomendaciones ────────────────────────────────

CREATE TABLE recomendaciones (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tipo_alerta VARCHAR(50) NOT NULL,
    texto       TEXT        NOT NULL,
    prioridad   INT         NOT NULL DEFAULT 1
);

-- ── Tabla: alertas_recomendaciones ───────────────────────
-- Clase de asociación: registra si el administrador
-- aplicó la recomendación y cuándo

CREATE TABLE alertas_recomendaciones (
    alerta_id        UUID        NOT NULL REFERENCES alertas(id) ON DELETE CASCADE,
    recomendacion_id UUID        NOT NULL REFERENCES recomendaciones(id) ON DELETE CASCADE,
    aplicada         BOOLEAN     NOT NULL DEFAULT FALSE,
    aplicada_at      TIMESTAMPTZ,
    PRIMARY KEY (alerta_id, recomendacion_id)
);

-- ── Índices ───────────────────────────────────────────────

CREATE INDEX idx_metricas_sistema    ON metricas_snapshot(sistema_id);
CREATE INDEX idx_metricas_timestamp  ON metricas_snapshot(timestamp DESC);
CREATE INDEX idx_ev_sis_sistema      ON eventos_sistema(sistema_id);
CREATE INDEX idx_ev_sis_timestamp    ON eventos_sistema(timestamp DESC);
CREATE INDEX idx_ev_web_servicio     ON eventos_web(servicio_web_id);
CREATE INDEX idx_ev_web_timestamp    ON eventos_web(timestamp DESC);
CREATE INDEX idx_alertas_timestamp   ON alertas(timestamp DESC);
CREATE INDEX idx_alertas_resuelta    ON alertas(resuelta);
CREATE INDEX idx_alertas_evento      ON alertas(evento_id);
CREATE INDEX idx_recs_tipo           ON recomendaciones(tipo_alerta);

-- ── Datos iniciales: recomendaciones ─────────────────────

INSERT INTO recomendaciones (tipo_alerta, texto, prioridad) VALUES
    ('cpu_alta',      'Revisar procesos activos con alto consumo de CPU. Considerar reinicio o escalado.', 1),
    ('ram_alta',      'Verificar consumo de memoria por proceso. Posible memory leak o falta de recursos.', 1),
    ('disco_alto',    'Liberar espacio en disco: limpiar logs, backups antiguos o ampliar capacidad.', 1),
    ('http_down',     'Servicio web inaccesible. Verificar estado del servidor y configuración de red.', 1),
    ('http_lento',    'Tiempo de respuesta elevado. Revisar carga del servidor y consultas a BD.', 2),
    ('login_fallido', 'Múltiples intentos fallidos detectados. Posible ataque de fuerza bruta. Revisar IPs.', 1),
    ('agente_caido',  'El agente no reporta. Verificar conectividad y estado del servicio.', 1);