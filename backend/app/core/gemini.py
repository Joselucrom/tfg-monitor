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
    tipo_evento:    str,
    valor:          float | None,
    severidad:      str,
    mensaje:        str,
    nombre_sistema: str | None = None,
) -> dict:
    client = _get_client()
    if not client:
        return {
            "analisis": "API key de Gemini no configurada.",
            "causas":   [],
            "acciones": [],
            "error":    "GEMINI_API_KEY no configurada.",
        }

    prompt = _construir_prompt(tipo_evento, valor, severidad, mensaje, nombre_sistema)

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


def _construir_prompt(tipo_evento, valor, severidad, mensaje, nombre_sistema):
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

    return f"""Eres un experto en administración de sistemas y seguridad informática.
Se ha generado una alerta de severidad {severidad.upper()} {contexto}.

Alerta detectada: {descripcion}
Mensaje del sistema: {mensaje}

Responde EXACTAMENTE en este formato, sin texto adicional:

ANALISIS:
[Un párrafo conciso de 2-3 frases explicando qué significa esta alerta y su impacto potencial]

CAUSAS:
- [causa 1]
- [causa 2]
- [causa 3]

ACCIONES:
- [acción recomendada 1]
- [acción recomendada 2]
- [acción recomendada 3]

Sé específico y práctico. Usa terminología técnica apropiada."""


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