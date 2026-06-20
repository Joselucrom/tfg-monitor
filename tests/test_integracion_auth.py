"""
Pruebas de integración — Autenticación y usuarios
====================================================
Verifica el flujo completo de registro, login y protección
de endpoints contra una base de datos PostgreSQL de test real.

IMPORTANTE: requiere la base de datos tfg_monitor_test activa.
Ejecutar con: pytest tests/test_integracion_auth.py -v
"""
import pytest


class TestRegistroUsuario:

    async def test_registrar_primer_usuario_como_admin(self, client):
        """El primer usuario del sistema puede registrarse como admin."""
        response = await client.post("/api/usuarios/", json={
            "nombre": "Admin Test",
            "email": "admin@test.com",
            "password": "1234",
            "rol": "admin",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "admin@test.com"
        assert data["rol"] == "admin"
        assert data["activo"] is True

    async def test_registrar_segundo_admin_falla(self, client):
        """No se puede registrar un segundo admin por la vía pública."""
        await client.post("/api/usuarios/", json={
            "nombre": "Admin 1", "email": "admin1@test.com",
            "password": "1234", "rol": "admin",
        })
        response = await client.post("/api/usuarios/", json={
            "nombre": "Admin 2", "email": "admin2@test.com",
            "password": "1234", "rol": "admin",
        })
        assert response.status_code == 403

    async def test_registrar_email_duplicado_falla(self, client):
        await client.post("/api/usuarios/", json={
            "nombre": "Usuario 1", "email": "duplicado@test.com",
            "password": "1234", "rol": "operador",
        })
        response = await client.post("/api/usuarios/", json={
            "nombre": "Usuario 2", "email": "duplicado@test.com",
            "password": "5678", "rol": "operador",
        })
        assert response.status_code == 400

    async def test_registrar_operador_sin_restriccion(self, client):
        """Pueden existir varios operadores sin restricción."""
        r1 = await client.post("/api/usuarios/", json={
            "nombre": "Op 1", "email": "op1@test.com",
            "password": "1234", "rol": "operador",
        })
        r2 = await client.post("/api/usuarios/", json={
            "nombre": "Op 2", "email": "op2@test.com",
            "password": "1234", "rol": "operador",
        })
        assert r1.status_code == 201
        assert r2.status_code == 201


class TestLogin:

    async def test_login_credenciales_correctas(self, client):
        await client.post("/api/usuarios/", json={
            "nombre": "Test", "email": "login@test.com",
            "password": "secreto123", "rol": "operador",
        })
        response = await client.post(
            "/api/auth/login",
            data={"username": "login@test.com", "password": "secreto123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_password_incorrecta(self, client):
        await client.post("/api/usuarios/", json={
            "nombre": "Test", "email": "login2@test.com",
            "password": "correcta", "rol": "operador",
        })
        response = await client.post(
            "/api/auth/login",
            data={"username": "login2@test.com", "password": "incorrecta"},
        )
        assert response.status_code == 401

    async def test_login_usuario_no_existe(self, client):
        response = await client.post(
            "/api/auth/login",
            data={"username": "noexiste@test.com", "password": "1234"},
        )
        assert response.status_code == 401


class TestProteccionEndpoints:

    async def test_endpoint_protegido_sin_token(self, client):
        """Un endpoint protegido sin token debe devolver 401."""
        response = await client.get("/api/sistemas/")
        assert response.status_code in (401, 403)

    async def test_endpoint_protegido_con_token_valido(self, client):
        await client.post("/api/usuarios/", json={
            "nombre": "Test", "email": "protegido@test.com",
            "password": "1234", "rol": "operador",
        })
        login = await client.post(
            "/api/auth/login",
            data={"username": "protegido@test.com", "password": "1234"},
        )
        token = login.json()["access_token"]

        response = await client.get(
            "/api/sistemas/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json() == []

    async def test_endpoint_admin_con_rol_operador_devuelve_403(self, client):
        """Un operador no puede acceder a endpoints exclusivos de admin."""
        await client.post("/api/usuarios/", json={
            "nombre": "Operador", "email": "operador@test.com",
            "password": "1234", "rol": "operador",
        })
        login = await client.post(
            "/api/auth/login",
            data={"username": "operador@test.com", "password": "1234"},
        )
        token = login.json()["access_token"]

        response = await client.get(
            "/api/admin/estadisticas",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    async def test_endpoint_admin_con_rol_admin_devuelve_200(self, client):
        await client.post("/api/usuarios/", json={
            "nombre": "Admin", "email": "admintest@test.com",
            "password": "1234", "rol": "admin",
        })
        login = await client.post(
            "/api/auth/login",
            data={"username": "admintest@test.com", "password": "1234"},
        )
        token = login.json()["access_token"]

        response = await client.get(
            "/api/admin/estadisticas",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200