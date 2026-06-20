"""
Pruebas de integración — Flujo completo del motor de reglas
==============================================================
Verifica el flujo end-to-end más importante del sistema:
crear sistema → crear regla → enviar evento → alerta generada
automáticamente con sus recomendaciones asociadas.

Ejecutar con: pytest tests/test_integracion_flujo.py -v
"""
import pytest


async def _crear_usuario_y_loguear(client, email="flujo@test.com"):
    """Helper: registra un usuario y devuelve su token de acceso."""
    await client.post("/api/usuarios/", json={
        "nombre": "Test Flujo", "email": email,
        "password": "1234", "rol": "operador",
    })
    login = await client.post(
        "/api/auth/login",
        data={"username": email, "password": "1234"},
    )
    return login.json()["access_token"]


class TestFlujoMotorReglas:

    async def test_evento_sin_regla_no_genera_alerta(self, client):
        """Un evento sin reglas activas para su métrica no debe generar alerta."""
        token = await _crear_usuario_y_loguear(client)
        headers = {"Authorization": f"Bearer {token}"}

        sistema = await client.post(
            "/api/sistemas/",
            json={"nombre": "srv-test", "ip": "10.0.0.1", "descripcion": "test"},
            headers=headers,
        )
        sistema_id = sistema.json()["id"]

        await client.post("/api/eventos/sistema", json={
            "sistema_id": sistema_id,
            "tipo": "cpu_alta",
            "valor": 50.0,
            "origen": "test",
        })

        alertas = await client.get("/api/alertas/", headers=headers)
        assert alertas.json() == []

    async def test_evento_que_supera_umbral_genera_alerta(self, client):
        """El caso principal: evento que cumple regla activa genera alerta."""
        token = await _crear_usuario_y_loguear(client, "flujo2@test.com")
        headers = {"Authorization": f"Bearer {token}"}

        sistema = await client.post(
            "/api/sistemas/",
            json={"nombre": "srv-test", "ip": "10.0.0.2", "descripcion": "test"},
            headers=headers,
        )
        sistema_id = sistema.json()["id"]

        regla = await client.post(
            "/api/reglas/",
            json={
                "nombre": "CPU crítica test", "metrica": "cpu_alta",
                "operador": ">", "umbral": 80.0, "severidad": "critical",
            },
            headers=headers,
        )
        assert regla.status_code == 201

        evento = await client.post("/api/eventos/sistema", json={
            "sistema_id": sistema_id,
            "tipo": "cpu_alta",
            "valor": 95.0,
            "origen": "test",
        })
        assert evento.status_code == 201

        alertas = await client.get("/api/alertas/?resuelta=false", headers=headers)
        data = alertas.json()
        assert len(data) == 1
        assert data[0]["severidad"] == "critical"

    async def test_evento_bajo_umbral_no_genera_alerta(self, client):
        """Un valor que no supera el umbral no debe generar alerta."""
        token = await _crear_usuario_y_loguear(client, "flujo3@test.com")
        headers = {"Authorization": f"Bearer {token}"}

        sistema = await client.post(
            "/api/sistemas/",
            json={"nombre": "srv-test", "ip": "10.0.0.3"},
            headers=headers,
        )
        sistema_id = sistema.json()["id"]

        await client.post(
            "/api/reglas/",
            json={
                "nombre": "RAM crítica", "metrica": "ram_alta",
                "operador": ">", "umbral": 90.0, "severidad": "critical",
            },
            headers=headers,
        )

        await client.post("/api/eventos/sistema", json={
            "sistema_id": sistema_id,
            "tipo": "ram_alta",
            "valor": 50.0,
            "origen": "test",
        })

        alertas = await client.get("/api/alertas/?resuelta=false", headers=headers)
        assert alertas.json() == []

    async def test_alerta_tiene_recomendaciones_asociadas(self, client):
        """La alerta generada debe traer asociadas las recomendaciones del catálogo."""
        token = await _crear_usuario_y_loguear(client, "flujo4@test.com")
        headers = {"Authorization": f"Bearer {token}"}

        sistema = await client.post(
            "/api/sistemas/",
            json={"nombre": "srv-test", "ip": "10.0.0.4"},
            headers=headers,
        )
        sistema_id = sistema.json()["id"]

        await client.post(
            "/api/reglas/",
            json={
                "nombre": "Disco lleno", "metrica": "disco_alto",
                "operador": ">", "umbral": 85.0, "severidad": "warning",
            },
            headers=headers,
        )

        await client.post("/api/eventos/sistema", json={
            "sistema_id": sistema_id,
            "tipo": "disco_alto",
            "valor": 92.0,
            "origen": "test",
        })

        alertas = await client.get("/api/alertas/?resuelta=false", headers=headers)
        alerta_id = alertas.json()[0]["id"]

        recs = await client.get(
            f"/api/alertas/{alerta_id}/recomendaciones",
            headers=headers,
        )
        assert recs.status_code == 200
        assert len(recs.json()) >= 1
        assert all(r["aplicada"] is False for r in recs.json())

    async def test_regla_desactivada_no_genera_alerta(self, client):
        """Una regla desactivada no debe evaluarse aunque su condición se cumpla."""
        token = await _crear_usuario_y_loguear(client, "flujo5@test.com")
        headers = {"Authorization": f"Bearer {token}"}

        sistema = await client.post(
            "/api/sistemas/",
            json={"nombre": "srv-test", "ip": "10.0.0.5"},
            headers=headers,
        )
        sistema_id = sistema.json()["id"]

        regla = await client.post(
            "/api/reglas/",
            json={
                "nombre": "Regla a desactivar", "metrica": "cpu_alta",
                "operador": ">", "umbral": 50.0, "severidad": "warning",
            },
            headers=headers,
        )
        regla_id = regla.json()["id"]

        # Desactivar la regla
        await client.patch(f"/api/reglas/{regla_id}/toggle", headers=headers)

        await client.post("/api/eventos/sistema", json={
            "sistema_id": sistema_id,
            "tipo": "cpu_alta",
            "valor": 99.0,
            "origen": "test",
        })

        alertas = await client.get("/api/alertas/?resuelta=false", headers=headers)
        assert alertas.json() == []

    async def test_resolver_alerta_actualiza_estado(self, client):
        """Resolver una alerta debe marcarla como resuelta con fecha registrada."""
        token = await _crear_usuario_y_loguear(client, "flujo6@test.com")
        headers = {"Authorization": f"Bearer {token}"}

        sistema = await client.post(
            "/api/sistemas/",
            json={"nombre": "srv-test", "ip": "10.0.0.6"},
            headers=headers,
        )
        sistema_id = sistema.json()["id"]

        await client.post(
            "/api/reglas/",
            json={
                "nombre": "Regla resolver", "metrica": "cpu_alta",
                "operador": ">", "umbral": 50.0, "severidad": "info",
            },
            headers=headers,
        )

        await client.post("/api/eventos/sistema", json={
            "sistema_id": sistema_id, "tipo": "cpu_alta",
            "valor": 99.0, "origen": "test",
        })

        alertas = await client.get("/api/alertas/?resuelta=false", headers=headers)
        alerta_id = alertas.json()[0]["id"]

        resolver = await client.post(
            f"/api/alertas/{alerta_id}/resolver", headers=headers
        )
        assert resolver.status_code == 200
        assert resolver.json()["resuelta"] is True
        assert resolver.json()["resuelta_at"] is not None

    async def test_resolver_alerta_ya_resuelta_falla(self, client):
        """No se puede resolver dos veces la misma alerta."""
        token = await _crear_usuario_y_loguear(client, "flujo7@test.com")
        headers = {"Authorization": f"Bearer {token}"}

        sistema = await client.post(
            "/api/sistemas/",
            json={"nombre": "srv-test", "ip": "10.0.0.7"},
            headers=headers,
        )
        sistema_id = sistema.json()["id"]

        await client.post(
            "/api/reglas/",
            json={
                "nombre": "Regla doble resolver", "metrica": "cpu_alta",
                "operador": ">", "umbral": 50.0, "severidad": "info",
            },
            headers=headers,
        )

        await client.post("/api/eventos/sistema", json={
            "sistema_id": sistema_id, "tipo": "cpu_alta",
            "valor": 99.0, "origen": "test",
        })

        alertas = await client.get("/api/alertas/?resuelta=false", headers=headers)
        alerta_id = alertas.json()[0]["id"]

        await client.post(f"/api/alertas/{alerta_id}/resolver", headers=headers)
        segundo_intento = await client.post(
            f"/api/alertas/{alerta_id}/resolver", headers=headers
        )
        assert segundo_intento.status_code == 400