-- ============================================================
-- Plataforma de Monitorización y Seguridad — TFG UCA
-- Diseño físico de datos — PostgreSQL
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";  -- para gen_random_uuid()

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

-- ── Tabla: usuarios ──────────────────────────────────────

CREATE TABLE usuarios (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre        VARCHAR(100)  NOT NULL,
    email         VARCHAR(150)  NOT NULL UNIQUE,
    password_hash VARCHAR(255)  NOT NULL,
    rol           rol_usuario   NOT NULL DEFAULT 'operador',
    activo        BOOLEAN       NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- ── Tabla: sistemas ──────────────────────────────────────

CREATE TABLE sistemas (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id       UUID          NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    nombre           VARCHAR(100)  NOT NULL,
    ip               VARCHAR(45),       -- IPv4 o IPv6
    descripcion      TEXT,
    activo           BOOLEAN       NOT NULL DEFAULT TRUE,
    ultimo_contacto  TIMESTAMPTZ,       -- última vez que el agente reportó
    created_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- ── Tabla: servicios_web ─────────────────────────────────

CREATE TABLE servicios_web (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id   UUID          NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    nombre       VARCHAR(100)  NOT NULL,
    url          TEXT          NOT NULL,
    intervalo_s  INT           NOT NULL DEFAULT 60,  -- segundos entre checks
    activo       BOOLEAN       NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- ── Tabla: reglas ─────────────────────────────────────────

CREATE TABLE reglas (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id   UUID            NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    nombre       VARCHAR(150)    NOT NULL,
    metrica      VARCHAR(50)     NOT NULL,   -- 'cpu', 'ram', 'http_status', etc.
    operador     operador_regla  NOT NULL,
    umbral       FLOAT           NOT NULL,
    severidad    severidad_alerta NOT NULL DEFAULT 'warning',
    activa       BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- ── Tabla: eventos ────────────────────────────────────────
-- sistema_id y servicio_web_id son mutuamente excluyentes (CHECK)

CREATE TABLE eventos (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sistema_id       UUID          REFERENCES sistemas(id) ON DELETE SET NULL,
    servicio_web_id  UUID          REFERENCES servicios_web(id) ON DELETE SET NULL,
    tipo             tipo_evento   NOT NULL,
    valor            FLOAT,                 -- valor numérico de la métrica
    origen           VARCHAR(100),          -- hostname o URL origen
    timestamp        TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    CONSTRAINT evento_origen_check
        CHECK (
            (sistema_id IS NOT NULL AND servicio_web_id IS NULL) OR
            (sistema_id IS NULL AND servicio_web_id IS NOT NULL)
        )
);

-- ── Tabla: alertas ────────────────────────────────────────

CREATE TABLE alertas (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evento_id    UUID             NOT NULL REFERENCES eventos(id) ON DELETE CASCADE,
    regla_id     UUID             NOT NULL REFERENCES reglas(id) ON DELETE CASCADE,
    severidad    severidad_alerta NOT NULL,
    mensaje      TEXT             NOT NULL,
    resuelta     BOOLEAN          NOT NULL DEFAULT FALSE,
    timestamp    TIMESTAMPTZ      NOT NULL DEFAULT NOW(),
    resuelta_at  TIMESTAMPTZ                              -- NULL si no resuelta
);

-- ── Tabla: recomendaciones ───────────────────────────────
-- Catálogo estático de recomendaciones por tipo de alerta

CREATE TABLE recomendaciones (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tipo_alerta  VARCHAR(50)  NOT NULL,   -- coincide con tipo_evento
    texto        TEXT         NOT NULL,
    prioridad    INT          NOT NULL DEFAULT 1
);

-- ── Tabla intermedia: alertas_recomendaciones ────────────

CREATE TABLE alertas_recomendaciones (
    alerta_id        UUID NOT NULL REFERENCES alertas(id) ON DELETE CASCADE,
    recomendacion_id UUID NOT NULL REFERENCES recomendaciones(id) ON DELETE CASCADE,
    PRIMARY KEY (alerta_id, recomendacion_id)
);

-- ── Índices de rendimiento ───────────────────────────────

CREATE INDEX idx_eventos_sistema      ON eventos(sistema_id);
CREATE INDEX idx_eventos_servicio     ON eventos(servicio_web_id);
CREATE INDEX idx_eventos_timestamp    ON eventos(timestamp DESC);
CREATE INDEX idx_alertas_timestamp    ON alertas(timestamp DESC);
CREATE INDEX idx_alertas_resuelta     ON alertas(resuelta);
CREATE INDEX idx_recomendaciones_tipo ON recomendaciones(tipo_alerta);

-- ── Datos iniciales: recomendaciones ─────────────────────

INSERT INTO recomendaciones (tipo_alerta, texto, prioridad) VALUES
    ('cpu_alta',      'Revisar procesos activos con alto consumo de CPU. Considerar reinicio o escalado.', 1),
    ('ram_alta',      'Verificar consumo de memoria por proceso. Posible memory leak o falta de recursos.', 1),
    ('disco_alto',    'Liberar espacio en disco: limpiar logs, backups antiguos o ampliar capacidad.', 1),
    ('http_down',     'Servicio web inaccesible. Verificar estado del servidor y configuración de red.', 1),
    ('http_lento',    'Tiempo de respuesta elevado. Revisar carga del servidor y consultas a BD.', 2),
    ('login_fallido', 'Múltiples intentos fallidos detectados. Posible ataque de fuerza bruta. Revisar IPs.', 1),
    ('agente_caido',  'El agente de monitorización no reporta. Verificar conectividad y estado del servicio.', 1);
