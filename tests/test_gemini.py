"""
Pruebas unitarias del módulo Gemini — TFG UCA
===============================================
Verifica el parseo de la respuesta estructurada de Gemini y la
construcción del prompt con contexto histórico, sin necesidad de
llamar a la API real (no se prueba la llamada de red, solo la
lógica de parseo y construcción de texto).

Ejecutar con: pytest tests/test_gemini.py -v
"""
from app.core.gemini import _parsear_respuesta, _construir_prompt


class TestParsearRespuesta:
    """Pruebas del parseo de la respuesta estructurada de Gemini."""

    def test_respuesta_bien_formada(self):
        texto = """ANALISIS:
El servidor presenta un uso elevado de CPU.

CAUSAS:
- Proceso con memory leak
- Carga de trabajo elevada
- Tarea programada en ejecución

ACCIONES:
- Ejecutar top para identificar el proceso
- Revisar logs del sistema
- Reiniciar el servicio si es necesario"""

        resultado = _parsear_respuesta(texto)

        assert resultado["error"] is None
        assert "uso elevado de CPU" in resultado["analisis"]
        assert len(resultado["causas"]) == 3
        assert len(resultado["acciones"]) == 3
        assert resultado["causas"][0] == "Proceso con memory leak"
        assert resultado["acciones"][0] == "Ejecutar top para identificar el proceso"

    def test_respuesta_sin_acciones(self):
        """Si Gemini no devuelve la sección ACCIONES, no debe fallar."""
        texto = """ANALISIS:
Análisis sin causas ni acciones específicas.

CAUSAS:
- Causa única detectada"""

        resultado = _parsear_respuesta(texto)

        assert "Análisis sin causas" in resultado["analisis"]
        assert len(resultado["causas"]) == 1
        assert resultado["acciones"] == []

    def test_respuesta_mal_formada_no_falla(self):
        """Texto sin el formato esperado debe caer en el análisis completo."""
        texto = "Esto es un texto libre sin las cabeceras esperadas."

        resultado = _parsear_respuesta(texto)

        assert resultado["analisis"] == texto
        assert resultado["causas"] == []
        assert resultado["acciones"] == []

    def test_respuesta_vacia(self):
        resultado = _parsear_respuesta("")
        assert resultado["causas"] == []
        assert resultado["acciones"] == []

    def test_lineas_con_guion_vacio_se_ignoran(self):
        """Las líneas que solo contienen '-' no deben generar elementos vacíos."""
        texto = """ANALISIS:
Texto de análisis.

CAUSAS:
- Causa real
-
- Otra causa real"""

        resultado = _parsear_respuesta(texto)
        assert len(resultado["causas"]) == 2
        assert "" not in resultado["causas"]


class TestConstruirPrompt:
    """
    Pruebas de la construcción del prompt enviado a Gemini.
    Firma real: _construir_prompt(tipo_evento, valor, severidad, mensaje,
                                   nombre_sistema, historial_valores, alertas_recientes)
    """

    def test_prompt_incluye_nombre_sistema(self):
        prompt = _construir_prompt(
            "cpu_alta", 95.0, "critical", "CPU crítica detectada",
            "servidor-01", [], 0,
        )
        assert "servidor-01" in prompt
        assert "CRITICAL" in prompt

    def test_prompt_sin_nombre_sistema(self):
        """Si no hay nombre de sistema, debe usar el genérico 'un servidor'."""
        prompt = _construir_prompt(
            "http_down", None, "warning", "Servicio caído",
            None, [], 0,
        )
        assert "en un servidor" in prompt
        assert "servicio web inaccesible" in prompt

    def test_prompt_tipo_evento_desconocido(self):
        """Un tipo de evento no mapeado debe usar su valor literal."""
        prompt = _construir_prompt(
            "tipo_nuevo_no_mapeado", 10.0, "info", "Evento desconocido",
            None, [], 0,
        )
        assert "tipo_nuevo_no_mapeado" in prompt

    def test_prompt_incluye_formato_de_respuesta_esperado(self):
        """El prompt debe pedir explícitamente el formato estructurado."""
        prompt = _construir_prompt(
            "ram_alta", 90.0, "warning", "RAM alta",
            "srv-01", [], 0,
        )
        assert "ANALISIS:" in prompt
        assert "CAUSAS:" in prompt
        assert "ACCIONES:" in prompt

    # ── Pruebas del contexto histórico ──────────────────

    def test_prompt_sin_historial_no_incluye_seccion(self):
        """Sin historial, el prompt no debe mencionar valores anteriores."""
        prompt = _construir_prompt(
            "cpu_alta", 90.0, "warning", "CPU alta",
            "srv-01", [], 0,
        )
        assert "Últimos valores registrados" not in prompt

    def test_prompt_con_historial_incluye_valores(self):
        """Con historial, el prompt debe listar los valores anteriores."""
        historial = [
            {"valor": 92.0, "timestamp": "t1"},
            {"valor": 88.0, "timestamp": "t2"},
            {"valor": 85.0, "timestamp": "t3"},
        ]
        prompt = _construir_prompt(
            "cpu_alta", 95.0, "critical", "CPU crítica",
            "srv-01", historial, 0,
        )
        assert "Últimos valores registrados" in prompt
        assert "92.0%" in prompt

    def test_prompt_detecta_tendencia_ascendente(self):
        """Si el valor más reciente es mayor que el más antiguo, debe marcar ASCENDENTE."""
        historial = [
            {"valor": 95.0, "timestamp": "t1"},  # más reciente
            {"valor": 80.0, "timestamp": "t2"},
            {"valor": 70.0, "timestamp": "t3"},  # más antiguo
        ]
        prompt = _construir_prompt(
            "cpu_alta", 95.0, "critical", "CPU crítica",
            "srv-01", historial, 0,
        )
        assert "ASCENDENTE" in prompt

    def test_prompt_detecta_tendencia_descendente(self):
        """Si el valor más reciente es menor que el más antiguo, debe marcar DESCENDENTE."""
        historial = [
            {"valor": 70.0, "timestamp": "t1"},  # más reciente
            {"valor": 85.0, "timestamp": "t2"},
            {"valor": 95.0, "timestamp": "t3"},  # más antiguo
        ]
        prompt = _construir_prompt(
            "cpu_alta", 70.0, "warning", "CPU bajando",
            "srv-01", historial, 0,
        )
        assert "DESCENDENTE" in prompt

    def test_prompt_detecta_tendencia_estable(self):
        """Si la diferencia es pequeña (<=5), debe marcar ESTABLE."""
        historial = [
            {"valor": 87.0, "timestamp": "t1"},
            {"valor": 86.0, "timestamp": "t2"},
            {"valor": 85.0, "timestamp": "t3"},
        ]
        prompt = _construir_prompt(
            "cpu_alta", 87.0, "warning", "CPU estable",
            "srv-01", historial, 0,
        )
        assert "ESTABLE" in prompt

    def test_prompt_sin_alertas_recientes_no_incluye_seccion(self):
        """Si alertas_recientes <= 1, no debe mencionar recurrencia."""
        prompt = _construir_prompt(
            "cpu_alta", 90.0, "warning", "CPU alta",
            "srv-01", [], 1,
        )
        assert "del mismo tipo en las últimas 24 horas" not in prompt

    def test_prompt_con_alertas_recientes_menciona_numero(self):
        prompt = _construir_prompt(
            "cpu_alta", 90.0, "warning", "CPU alta",
            "srv-01", [], 3,
        )
        assert "alerta número 3" in prompt

    def test_prompt_alertas_muy_recurrentes_marca_estructural(self):
        """A partir de 5 alertas recurrentes, debe advertir de causa estructural."""
        prompt = _construir_prompt(
            "cpu_alta", 90.0, "critical", "CPU alta recurrente",
            "srv-01", [], 6,
        )
        assert "RECURRENTE" in prompt
        assert "causa estructural" in prompt