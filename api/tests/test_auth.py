"""
Integration tests for Auth API routes.
Tests registration, login, token refresh, and profile endpoints.
"""
import pytest
from httpx import AsyncClient


class TestRegister:
    """Test POST /api/v1/auth/register."""

    @pytest.mark.integration
    async def test_register_success(self, client: AsyncClient, user_data: dict):
        resp = await client.post("/api/v1/auth/register", json=user_data)
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == user_data["email"]
        assert data["full_name"] == user_data["full_name"]
        assert "id" in data
        assert "password" not in data  # password should never be returned

    @pytest.mark.integration
    async def test_register_duplicate_email(self, client: AsyncClient, user_data: dict):
        await client.post("/api/v1/auth/register", json=user_data)
        resp = await client.post("/api/v1/auth/register", json=user_data)
        assert resp.status_code in (409, 400)

    @pytest.mark.edge
    async def test_register_missing_email(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/register",
            json={"password": "Test1234!", "full_name": "No Email"},
        )
        assert resp.status_code == 422

    @pytest.mark.edge
    async def test_register_invalid_email(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "password": "Test1234!", "full_name": "Bad Email"},
        )
        assert resp.status_code == 422

    @pytest.mark.edge
    async def test_register_weak_password(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "weak@test.com", "password": "123", "full_name": "Weak PW"},
        )
        assert resp.status_code == 422

    @pytest.mark.edge
    async def test_register_empty_body(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/register", json={})
        assert resp.status_code == 422

    @pytest.mark.edge
    async def test_register_extra_fields_ignored(self, client: AsyncClient, user_data: dict):
        data = {**user_data, "is_superuser": True, "extra_field": "hacker"}
        resp = await client.post("/api/v1/auth/register", json=data)
        assert resp.status_code == 201
        result = resp.json()
        # is_superuser should not be settable via register
        assert result.get("is_superuser") is not True


class TestLogin:
    """Test POST /api/v1/auth/login."""

    @pytest.mark.integration
    async def test_login_success(self, client: AsyncClient, user_data: dict):
        await client.post("/api/v1/auth/register", json=user_data)
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": user_data["email"], "password": user_data["password"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.integration
    async def test_login_wrong_password(self, client: AsyncClient, user_data: dict):
        await client.post("/api/v1/auth/register", json=user_data)
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": user_data["email"], "password": "WrongPassword1!"},
        )
        assert resp.status_code == 401

    @pytest.mark.integration
    async def test_login_nonexistent_user(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "noone@test.com", "password": "Whatever1!"},
        )
        assert resp.status_code == 401

    @pytest.mark.edge
    async def test_login_missing_fields(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/login", json={"email": "a@b.com"})
        assert resp.status_code == 422


class TestRefresh:
    """Test POST /api/v1/auth/refresh."""

    @pytest.mark.integration
    async def test_refresh_success(self, client: AsyncClient, registered_user: dict):
        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": registered_user["refresh_token"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data

    @pytest.mark.edge
    async def test_refresh_invalid_token(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )
        assert resp.status_code == 401


class TestMe:
    """Test GET /api/v1/auth/me."""

    @pytest.mark.integration
    async def test_me_authenticated(self, client: AsyncClient, auth_headers: dict, user_data: dict):
        resp = await client.get("/api/v1/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == user_data["email"]

    @pytest.mark.integration
    async def test_me_unauthenticated(self, client: AsyncClient):
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code in (401, 403)

    @pytest.mark.edge
    async def test_me_expired_token(self, client: AsyncClient):
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer expired.token.here"},
        )
        assert resp.status_code in (401, 403)

    @pytest.mark.edge
    async def test_me_malformed_header(self, client: AsyncClient):
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "NotBearer token"},
        )
        assert resp.status_code in (401, 403)
