"""
Agente de monitorización v2 — TFG UCA
======================================
Recoge métricas del servidor y estado de servicios web,
y los envía al backend en cada ciclo.

Ciclo de cada iteración:
  1. Guarda un MetricaSnapshot (CPU, RAM, disco)
  2. Si alguna métrica supera el umbral interno, envía un EventoSistema
  3. Comprueba los servicios web configurados y envía EventoWeb si hay problemas

Variables de entorno:
  BACKEND_URL   → URL base del backend (default: http://localhost:8000)
  SISTEMA_ID    → UUID del sistema registrado en la BD (obligatorio)
  INTERVALO     → segundos entre ciclos (default: 30)
  URLS_VIGILAR  → URLs separadas por coma a monitorizar (opcional)
  UMBRAL_CPU    → porcentaje de CPU para generar evento (default: 85)
  UMBRAL_RAM    → porcentaje de RAM para generar evento (default: 85)
  UMBRAL_DISCO  → porcentaje de disco para generar evento (default: 85)
  TIMEOUT_HTTP  → segundos máx para considerar un servicio lento (default: 2)
"""

import os
import time
import socket
import httpx
import psutil
from datetime import datetime


# ── Configuración desde variables de entorno ──────────────

BACKEND_URL  = os.getenv("BACKEND_URL", "http://localhost:8000")
SISTEMA_ID   = os.getenv("SISTEMA_ID", "")
INTERVALO    = int(os.getenv("INTERVALO", "30"))
URLS_VIGILAR = [u.strip() for u in os.getenv("URLS_VIGILAR", "").split(",") if u.strip()]
UMBRAL_CPU   = float(os.getenv("UMBRAL_CPU",  "85"))
UMBRAL_RAM   = float(os.getenv("UMBRAL_RAM",  "85"))
UMBRAL_DISCO = float(os.getenv("UMBRAL_DISCO", "85"))
TIMEOUT_HTTP = float(os.getenv("TIMEOUT_HTTP", "2"))
HOSTNAME     = socket.gethostname()


# ── Helpers de log ────────────────────────────────────────

def log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")


def log_error(msg: str) -> None:
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ❌ {msg}")

# ══════════════════════════════════════════════════════════
# Detectar IP local del servidor
# ══════════════════════════════════════════════════════════

def detectar_ip_local() -> str:
    """Detecta la IP local del servidor donde corre el agente."""
    try:
        # Conecta a un servidor externo sin enviar datos
        # solo para obtener la IP local del interfaz de red
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return socket.gethostbyname(socket.gethostname())

# ══════════════════════════════════════════════════════════
# 1. Métricas del sistema — MetricaSnapshot
# ══════════════════════════════════════════════════════════

def recoger_metricas() -> dict:
    """Recoge CPU, RAM y disco del servidor."""
    cpu   = psutil.cpu_percent(interval=1)
    ram   = psutil.virtual_memory().percent
    disco = psutil.disk_usage("/").percent
    return {
        "cpu_percent":   cpu,
        "ram_percent":   ram,
        "disco_percent": disco,
    }


def enviar_snapshot(client: httpx.Client, metricas: dict) -> bool:
    """Envía un MetricaSnapshot al backend."""
    payload = {"sistema_id": SISTEMA_ID, **metricas}
    try:
        r = client.post(f"{BACKEND_URL}/api/metricas/", json=payload)
        if r.status_code == 201:
            log(f"Snapshot guardado — CPU:{metricas['cpu_percent']}% "
                f"RAM:{metricas['ram_percent']}% "
                f"Disco:{metricas['disco_percent']}%")
            return True
        log_error(f"Error al guardar snapshot: {r.status_code} {r.text}")
        return False
    except httpx.RequestError as e:
        log_error(f"Sin conexión al backend: {e}")
        return False


# ══════════════════════════════════════════════════════════
# 2. Eventos de sistema — EventoSistema
# ══════════════════════════════════════════════════════════

def evaluar_y_enviar_eventos_sistema(client: httpx.Client, metricas: dict) -> None:
    """
    Compara cada métrica con su umbral.
    Si lo supera, envía un EventoSistema al backend,
    que disparará el motor de reglas automáticamente.
    """
    checks = [
        ("cpu_alta",   metricas["cpu_percent"],   UMBRAL_CPU),
        ("ram_alta",   metricas["ram_percent"],   UMBRAL_RAM),
        ("disco_alto", metricas["disco_percent"], UMBRAL_DISCO),
    ]

    for tipo, valor, umbral in checks:
        if valor > umbral:
            _enviar_evento_sistema(client, tipo, valor)


def _enviar_evento_sistema(
    client: httpx.Client,
    tipo: str,
    valor: float,
    proceso: str | None = None,
    pid: int | None = None,
) -> None:
    """Envía un EventoSistema al backend."""
    payload = {
        "sistema_id": SISTEMA_ID,
        "tipo":       tipo,
        "valor":      valor,
        "origen":     HOSTNAME,
        "proceso":    proceso,
        "pid":        pid,
        "metadata":   {"agente_version": "2.0"},
    }
    try:
        r = client.post(f"{BACKEND_URL}/api/eventos/sistema", json=payload)
        if r.status_code == 201:
            log(f"Evento enviado: {tipo} = {valor}%")
        else:
            log_error(f"Error al enviar evento {tipo}: {r.status_code} {r.text}")
    except httpx.RequestError as e:
        log_error(f"Sin conexión al backend: {e}")


# ══════════════════════════════════════════════════════════
# 3. Checks HTTP — EventoWeb
# ══════════════════════════════════════════════════════════

def check_servicios_web(client: httpx.Client) -> None:
    """
    Comprueba cada URL configurada en URLS_VIGILAR.
    Envía EventoWeb si el servicio está caído o responde lento.
    """
    if not URLS_VIGILAR:
        return

    for url in URLS_VIGILAR:
        _check_url(client, url)


def _check_url(client: httpx.Client, url: str) -> None:
    """Hace un GET a la URL y evalúa la respuesta."""
    # Necesitamos el servicio_web_id — en producción se obtendría
    # de la API consultando la URL. Para simplificar usamos un
    # endpoint de búsqueda por URL.
    servicio_web_id = _buscar_servicio_web_id(client, url)
    if not servicio_web_id:
        log_error(f"No se encontró servicio web para URL: {url}")
        return

    try:
        inicio = time.time()
        r = client.get(url, timeout=TIMEOUT_HTTP * 2, follow_redirects=True)
        tiempo_ms = int((time.time() - inicio) * 1000)

        if not r.is_success:
            # Servicio caído o error HTTP
            _enviar_evento_web(client, servicio_web_id, "http_down",
                               http_status=r.status_code, tiempo_ms=tiempo_ms,
                               origen=url)
            log(f"HTTP DOWN: {url} → {r.status_code}")

        elif tiempo_ms > TIMEOUT_HTTP * 1000:
            # Servicio lento
            _enviar_evento_web(client, servicio_web_id, "http_lento",
                               http_status=r.status_code, tiempo_ms=tiempo_ms,
                               origen=url)
            log(f"HTTP LENTO: {url} → {tiempo_ms}ms")

        else:
            log(f"HTTP OK: {url} → {r.status_code} ({tiempo_ms}ms)")

    except httpx.TimeoutException:
        _enviar_evento_web(client, servicio_web_id, "http_down",
                           http_status=0, tiempo_ms=int(TIMEOUT_HTTP * 2000),
                           origen=url)
        log_error(f"HTTP TIMEOUT: {url}")

    except httpx.RequestError as e:
        _enviar_evento_web(client, servicio_web_id, "http_down",
                           http_status=0, tiempo_ms=0, origen=url)
        log_error(f"HTTP ERROR: {url} — {e}")


def _buscar_servicio_web_id(client: httpx.Client, url: str) -> str | None:
    """Consulta el backend para obtener el UUID del servicio web por URL."""
    try:
        r = client.get(f"{BACKEND_URL}/api/servicios-web/buscar",
                       params={"url": url}, timeout=5)
        if r.status_code == 200:
            return r.json().get("id")
    except httpx.RequestError:
        pass
    return None


def _enviar_evento_web(
    client: httpx.Client,
    servicio_web_id: str,
    tipo: str,
    http_status: int,
    tiempo_ms: int,
    origen: str,
) -> None:
    """Envía un EventoWeb al backend."""
    payload = {
        "servicio_web_id": servicio_web_id,
        "tipo":            tipo,
        "origen":          origen,
        "http_status":     http_status,
        "tiempo_ms":       tiempo_ms,
        "metadata":        {"agente_version": "2.0"},
    }
    try:
        r = client.post(f"{BACKEND_URL}/api/eventos/web", json=payload)
        if r.status_code != 201:
            log_error(f"Error al enviar EventoWeb: {r.status_code} {r.text}")
    except httpx.RequestError as e:
        log_error(f"Sin conexión al backend: {e}")


# ══════════════════════════════════════════════════════════
# Bucle principal
# ══════════════════════════════════════════════════════════

def main() -> None:
    if not SISTEMA_ID:
        log_error("SISTEMA_ID no configurado.")
        return

    log(f"Agente iniciado — sistema: {SISTEMA_ID} — intervalo: {INTERVALO}s")
    log(f"Umbrales → CPU:{UMBRAL_CPU}% RAM:{UMBRAL_RAM}% Disco:{UMBRAL_DISCO}%")

    # Detectar y registrar IP automáticamente al arrancar
    ip_local = detectar_ip_local()
    log(f"IP detectada: {ip_local}")
    try:
        with httpx.Client(timeout=5) as client:
            r = client.patch(
                f"{BACKEND_URL}/api/sistemas/{SISTEMA_ID}/ip",
                json={"ip": ip_local}
            )
            if r.status_code == 200:
                log(f"IP actualizada en el sistema: {ip_local}")
            else:
                log_error(f"No se pudo actualizar la IP: {r.status_code}")
    except httpx.RequestError as e:
        log_error(f"No se pudo conectar al backend para actualizar IP: {e}")

    if URLS_VIGILAR:
        log(f"URLs vigiladas: {', '.join(URLS_VIGILAR)}")

    while True:
        with httpx.Client(timeout=10) as client:
            # 1. Recoger y guardar snapshot
            metricas = recoger_metricas()
            enviar_snapshot(client, metricas)

            # 2. Evaluar umbrales y enviar eventos de sistema si procede
            evaluar_y_enviar_eventos_sistema(client, metricas)

            # 3. Comprobar servicios web
            check_servicios_web(client)

        log(f"Ciclo completado — próximo en {INTERVALO}s")
        time.sleep(INTERVALO)


if __name__ == "__main__":
    main()