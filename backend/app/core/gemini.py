from google import genai
from google.genai import types
from app.core.config import settings

_client = None

def _get_client():
    global _client
    if _client is None and settings.gemini_api_key:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


async def analizar_alerta(
    tipo_evento:       str,
    valor:             float | None,
    severidad:         str,
    mensaje:           str,
    nombre_sistema:    str | None = None,
    historial_valores: list       = None,
    alertas_recientes: int        = 0,
) -> dict:
    client = _get_client()
    if not client:
        return {
            "analisis": "API key de Gemini no configurada.",
            "causas":   [],
            "acciones": [],
            "error":    "GEMINI_API_KEY no configurada.",
        }

    prompt = _construir_prompt(
        tipo_evento, valor, severidad, mensaje,
        nombre_sistema, historial_valores or [], alertas_recientes
    )

    try:
        response = client.models.generate_content(
            model    = "models/gemini-3.1-flash-lite",
            contents = prompt,
        )
        return _parsear_respuesta(response.text.strip())
    except Exception as e:
        return {
            "analisis": "No se pudo obtener el análisis de Gemini.",
            "causas":   [],
            "acciones": [],
            "error":    str(e),
        }


def _construir_prompt(
    tipo_evento, valor, severidad, mensaje,
    nombre_sistema, historial_valores, alertas_recientes
):
    contexto = f"en el servidor '{nombre_sistema}'" if nombre_sistema else "en un servidor"
    valor_str = f"{valor:.1f}%" if valor is not None else "valor no disponible"

    descripciones = {
        "cpu_alta":      f"uso de CPU al {valor_str}",
        "ram_alta":      f"uso de RAM al {valor_str}",
        "disco_alto":    f"uso de disco al {valor_str}",
        "http_down":     "servicio web inaccesible",
        "http_lento":    f"tiempo de respuesta HTTP de {valor_str}ms",
        "login_fallido": f"{valor_str} intentos de login fallidos",
        "agente_caido":  "agente de monitorización sin respuesta",
    }
    descripcion = descripciones.get(tipo_evento, tipo_evento)

    # Construir sección de historial
    historial_str = ""
    if historial_valores:
        valores = [f"{h['valor']:.1f}%" for h in historial_valores]
        historial_str = f"\nÚltimos valores registrados: {', '.join(valores)}"
        if len(historial_valores) >= 3:
            tendencia = historial_valores[0]['valor'] - historial_valores[-1]['valor']
            if tendencia > 5:
                historial_str += " (tendencia ASCENDENTE — empeorando)"
            elif tendencia < -5:
                historial_str += " (tendencia DESCENDENTE — mejorando)"
            else:
                historial_str += " (tendencia ESTABLE)"

    # Contexto de alertas recientes
    alertas_str = ""
    if alertas_recientes > 1:
        alertas_str = f"\nEsta es la alerta número {alertas_recientes} del mismo tipo en las últimas 24 horas."
        if alertas_recientes >= 5:
            alertas_str += " El problema es RECURRENTE y puede indicar una causa estructural."

    return f"""Eres un experto en administración de sistemas y seguridad informática.
Se ha generado una alerta de severidad {severidad.upper()} {contexto}.

Alerta detectada: {descripcion}
Mensaje del sistema: {mensaje}{historial_str}{alertas_str}

Basándote en el contexto histórico proporcionado, genera un análisis ESPECÍFICO para esta situación concreta.
No uses respuestas genéricas — adapta el diagnóstico a los valores y tendencia observados.

Responde EXACTAMENTE en este formato, sin texto adicional:

ANALISIS:
[Un párrafo específico de 2-3 frases que tenga en cuenta los valores históricos y la tendencia]

CAUSAS:
- [causa específica basada en los datos]
- [causa específica basada en los datos]
- [causa específica basada en los datos]

ACCIONES:
- [acción concreta con comandos si procede]
- [acción concreta con comandos si procede]
- [acción concreta con comandos si procede]

Sé específico y práctico. Incluye comandos Linux cuando sea relevante."""


def _parsear_respuesta(texto: str) -> dict:
    resultado = {"analisis": "", "causas": [], "acciones": [], "error": None}
    try:
        secciones = texto.split("\n\n")
        for seccion in secciones:
            lineas  = seccion.strip().split("\n")
            if not lineas:
                continue
            cabecera = lineas[0].strip().upper()
            if cabecera.startswith("ANALISIS"):
                resultado["analisis"] = "\n".join(lineas[1:]).strip()
            elif cabecera.startswith("CAUSAS"):
                resultado["causas"] = [l.lstrip("- ").strip() for l in lineas[1:] if l.strip() and l.strip() != "-"]
            elif cabecera.startswith("ACCIONES"):
                resultado["acciones"] = [l.lstrip("- ").strip() for l in lineas[1:] if l.strip() and l.strip() != "-"]
        if not resultado["analisis"] and not resultado["causas"]:
            resultado["analisis"] = texto
    except Exception:
        resultado["analisis"] = texto
    return resultado