import pytest


async def _crear_usuario_y_loguear(client, email="restr@test.com"):
    await client.post("/api/usuarios/", json={
        "nombre": "Test Restr", "email": email,
        "password": "1234", "rol": "operador",
    })
    login = await client.post(
        "/api/auth/login",
        data={"username": email, "password": "1234"},
    )
    return login.json()["access_token"]


class TestEventosRestricciones:

    async def test_http_down_valor_binario_genera_alerta(self, client):
        token = await _crear_usuario_y_loguear(client, "down@test.com")
        headers = {"Authorization": f"Bearer {token}"}

        servicio = await client.post(
            "/api/servicios-web/",
            json={"nombre": "svc-down", "url": "http://down.test", "intervalo_s": 60},
            headers=headers,
        )
        svc_id = servicio.json()["id"]

        # Crear regla que espere valor == 1.0 para http_down
        await client.post(
            "/api/reglas/",
            json={
                "nombre": "HTTP down binario", "metrica": "http_down",
                "operador": "=", "umbral": 1.0, "severidad": "critical",
            },
            headers=headers,
        )

        # Enviar evento web con valor 1.0
        ev = await client.post(
            "/api/eventos/web",
            json={
                "servicio_web_id": svc_id,
                "tipo": "http_down",
                "valor": 1.0,
                "origen": "agent",
                "http_status": 0,
                "tiempo_ms": 0,
            },
        )
        assert ev.status_code == 201

        # Comprobar que se generó la alerta para el usuario
        alertas = await client.get("/api/alertas/?resuelta=false", headers=headers)
        data = alertas.json()
        assert len(data) == 1
        assert data[0]["severidad"] == "critical"

    async def test_servicio_buscar_devuelve_intervalo(self, client):
        token = await _crear_usuario_y_loguear(client, "int@test.com")
        headers = {"Authorization": f"Bearer {token}"}

        servicio = await client.post(
            "/api/servicios-web/",
            json={"nombre": "svc-int", "url": "http://int.test", "intervalo_s": 15},
            headers=headers,
        )
        # Buscar por URL sin JWT
        r = await client.get("/api/servicios-web/buscar", params={"url": "http://int.test"})
        assert r.status_code == 200
        assert r.json().get("intervalo_s") == 15

    async def test_eventos_rechazados_para_sistema_inactivo(self, client):
        token = await _crear_usuario_y_loguear(client, "inactive@test.com")
        headers = {"Authorization": f"Bearer {token}"}

        sistema = await client.post(
            "/api/sistemas/",
            json={"nombre": "srv-inactive", "ip": "10.0.0.9"},
            headers=headers,
        )
        sistema_id = sistema.json()["id"]

        # Desactivar el sistema
        await client.patch(f"/api/sistemas/{sistema_id}", json={"activo": False}, headers=headers)

        ev = await client.post("/api/eventos/sistema", json={
            "sistema_id": sistema_id,
            "tipo": "cpu_alta",
            "valor": 99.0,
            "origen": "test",
        })
        assert ev.status_code == 403
