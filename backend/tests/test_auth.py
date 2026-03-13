"""Tests for authentication endpoints: register and login."""
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_register_new_user(client: AsyncClient):
    resp = await client.post(
        "/auth/register",
        json={"email": "new@example.com", "password": "strongpass1"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "new@example.com"
    assert "id" in data
    assert "hashed_password" not in data  # never expose password hash


async def test_register_duplicate_email(client: AsyncClient):
    payload = {"email": "dup@example.com", "password": "strongpass1"}
    await client.post("/auth/register", json=payload)
    resp = await client.post("/auth/register", json=payload)
    assert resp.status_code == 409


async def test_register_short_password(client: AsyncClient):
    resp = await client.post(
        "/auth/register",
        json={"email": "short@example.com", "password": "abc"},
    )
    assert resp.status_code == 422


async def test_login_valid_credentials(client: AsyncClient):
    await client.post(
        "/auth/register",
        json={"email": "login@example.com", "password": "validpass1"},
    )
    resp = await client.post(
        "/auth/login",
        data={"username": "login@example.com", "password": "validpass1"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(client: AsyncClient):
    await client.post(
        "/auth/register",
        json={"email": "wrongpw@example.com", "password": "correctpass1"},
    )
    resp = await client.post(
        "/auth/login",
        data={"username": "wrongpw@example.com", "password": "wrongpassword"},
    )
    assert resp.status_code == 401


async def test_login_unknown_email(client: AsyncClient):
    resp = await client.post(
        "/auth/login",
        data={"username": "ghost@example.com", "password": "doesntmatter"},
    )
    assert resp.status_code == 401


async def test_protected_endpoint_without_token(client: AsyncClient):
    resp = await client.get("/stories")
    assert resp.status_code == 401


async def test_protected_endpoint_with_invalid_token(client: AsyncClient):
    resp = await client.get(
        "/stories", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert resp.status_code == 401


async def test_email_normalized_to_lowercase(client: AsyncClient):
    await client.post(
        "/auth/register",
        json={"email": "Upper@Example.COM", "password": "somepass1"},
    )
    resp = await client.post(
        "/auth/login",
        data={"username": "upper@example.com", "password": "somepass1"},
    )
    assert resp.status_code == 200
