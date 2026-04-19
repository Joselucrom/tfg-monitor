"""
Agente de monitorización — TFG UCA
Recoge métricas del sistema y las envía al backend cada N segundos.
"""
import time
import httpx
import psutil
import os
from datetime import datetime

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
SISTEMA_ID  = os.getenv("SISTEMA_ID", "")   # UUID del sistema registrado en la BD
INTERVALO   = int(os.getenv("INTERVALO", "30"))  # segundos


def get_metricas() -> list[dict]:
    """Recoge CPU, RAM y disco del sistema."""
    return [
        {
            "sistema_id": SISTEMA_ID,
            "tipo": "cpu_alta",
            "valor": psutil.cpu_percent(interval=1),
            "origen": "agente",
        },
        {
            "sistema_id": SISTEMA_ID,
            "tipo": "ram_alta",
            "valor": psutil.virtual_memory().percent,
            "origen": "agente",
        },
        {
            "sistema_id": SISTEMA_ID,
            "tipo": "disco_alto",
            "valor": psutil.disk_usage("/").percent,
            "origen": "agente",
        },
    ]


def enviar_eventos(eventos: list[dict]) -> None:
    """Envía una lista de eventos al backend."""
    try:
        with httpx.Client(timeout=5) as client:
            for evento in eventos:
                r = client.post(f"{BACKEND_URL}/api/eventos/", json=evento)
                if r.status_code not in (200, 201):
                    print(f"[{datetime.now()}] Error al enviar evento: {r.text}")
    except httpx.RequestError as e:
        print(f"[{datetime.now()}] No se pudo conectar al backend: {e}")


def main():
    print(f"[{datetime.now()}] Agente iniciado — intervalo: {INTERVALO}s")
    while True:
        metricas = get_metricas()
        enviar_eventos(metricas)
        print(f"[{datetime.now()}] {len(metricas)} métricas enviadas")
        time.sleep(INTERVALO)


if __name__ == "__main__":
    main()
