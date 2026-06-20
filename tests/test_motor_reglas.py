"""
Pruebas unitarias del motor de reglas — TFG UCA
=================================================
Verifica la lógica de evaluación de condiciones del motor de reglas,
aislada de la base de datos. Son funciones puras y por tanto
las más adecuadas para pruebas unitarias clásicas.

Ejecutar con: pytest tests/test_motor_reglas.py -v
"""
import pytest
from app.routers.eventos import _cumple_condicion


class TestCumpleCondicion:
    """Pruebas del operador de comparación del motor de reglas."""

    # ── Operador > ──────────────────────────────────────

    def test_mayor_que_cumple(self):
        assert _cumple_condicion(95.0, ">", 80.0) is True

    def test_mayor_que_no_cumple(self):
        assert _cumple_condicion(70.0, ">", 80.0) is False

    def test_mayor_que_valor_igual_umbral(self):
        """Con > estricto, el valor igual al umbral NO debe cumplir."""
        assert _cumple_condicion(80.0, ">", 80.0) is False

    # ── Operador < ──────────────────────────────────────

    def test_menor_que_cumple(self):
        assert _cumple_condicion(10.0, "<", 20.0) is True

    def test_menor_que_no_cumple(self):
        assert _cumple_condicion(30.0, "<", 20.0) is False

    # ── Operador >= ─────────────────────────────────────

    def test_mayor_igual_cumple_por_mayor(self):
        assert _cumple_condicion(90.0, ">=", 85.0) is True

    def test_mayor_igual_cumple_por_igualdad(self):
        assert _cumple_condicion(85.0, ">=", 85.0) is True

    def test_mayor_igual_no_cumple(self):
        assert _cumple_condicion(80.0, ">=", 85.0) is False

    # ── Operador <= ─────────────────────────────────────

    def test_menor_igual_cumple_por_menor(self):
        assert _cumple_condicion(5.0, "<=", 10.0) is True

    def test_menor_igual_cumple_por_igualdad(self):
        assert _cumple_condicion(10.0, "<=", 10.0) is True

    def test_menor_igual_no_cumple(self):
        assert _cumple_condicion(15.0, "<=", 10.0) is False

    # ── Operador = ──────────────────────────────────────

    def test_igual_cumple(self):
        assert _cumple_condicion(1.0, "=", 1.0) is True

    def test_igual_no_cumple(self):
        assert _cumple_condicion(2.0, "=", 1.0) is False

    # ── Casos límite ─────────────────────────────────────

    def test_operador_no_reconocido_devuelve_false(self):
        """Un operador inválido no debe lanzar excepción, solo no cumplir."""
        assert _cumple_condicion(50.0, "!=", 50.0) is False

    def test_valor_cero(self):
        assert _cumple_condicion(0.0, ">", -1.0) is True

    def test_valor_negativo(self):
        assert _cumple_condicion(-5.0, "<", 0.0) is True

    @pytest.mark.parametrize("valor,operador,umbral,esperado", [
        (100.0, ">",  99.9, True),
        (99.9,  ">",  100.0, False),
        (50.0,  ">=", 50.0, True),
        (49.99, ">=", 50.0, False),
    ])
    def test_casos_limite_decimales(self, valor, operador, umbral, esperado):
        """Verifica el comportamiento con valores decimales cercanos al umbral."""
        assert _cumple_condicion(valor, operador, umbral) is esperado