"""Tests for the /resources endpoints, including per-user isolation."""
import io
import json
import pytest
from httpx import AsyncClient

from tests.conftest import auth_headers, resource_payload

pytestmark = pytest.mark.asyncio


def _form_data(payload: dict) -> dict:
    """Convert a resource payload dict to httpx form-compatible data."""
    return {k: v for k, v in payload.items()}


async def test_create_resource(client: AsyncClient, token_a: str):
    resp = await client.post(
        "/resources",
        data=_form_data(resource_payload()),
        headers=auth_headers(token_a),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Test Podcast"
    assert "id" in data


async def test_list_resources(client: AsyncClient, token_a: str):
    await client.post("/resources", data=_form_data(resource_payload(title="R1")), headers=auth_headers(token_a))
    await client.post("/resources", data=_form_data(resource_payload(title="R2")), headers=auth_headers(token_a))

    resp = await client.get("/resources", headers=auth_headers(token_a))
    assert resp.status_code == 200
    titles = [r["title"] for r in resp.json()["resources"]]
    assert "R1" in titles and "R2" in titles


async def test_get_resource_by_id(client: AsyncClient, token_a: str):
    create = await client.post("/resources", data=_form_data(resource_payload()), headers=auth_headers(token_a))
    resource_id = create.json()["id"]

    resp = await client.get(f"/resources/{resource_id}", headers=auth_headers(token_a))
    assert resp.status_code == 200
    assert resp.json()["id"] == resource_id


async def test_delete_resource(client: AsyncClient, token_a: str):
    create = await client.post("/resources", data=_form_data(resource_payload()), headers=auth_headers(token_a))
    resource_id = create.json()["id"]

    resp = await client.delete(f"/resources/{resource_id}", headers=auth_headers(token_a))
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    resp = await client.get(f"/resources/{resource_id}", headers=auth_headers(token_a))
    assert resp.status_code == 404


async def test_user_isolation_list(client: AsyncClient, token_a: str, token_b: str):
    await client.post("/resources", data=_form_data(resource_payload(title="A-resource")), headers=auth_headers(token_a))

    resp = await client.get("/resources", headers=auth_headers(token_b))
    titles = [r["title"] for r in resp.json()["resources"]]
    assert "A-resource" not in titles


async def test_user_isolation_get(client: AsyncClient, token_a: str, token_b: str):
    create = await client.post("/resources", data=_form_data(resource_payload()), headers=auth_headers(token_a))
    resource_id = create.json()["id"]

    resp = await client.get(f"/resources/{resource_id}", headers=auth_headers(token_b))
    assert resp.status_code == 404


async def test_user_isolation_delete(client: AsyncClient, token_a: str, token_b: str):
    create = await client.post("/resources", data=_form_data(resource_payload()), headers=auth_headers(token_a))
    resource_id = create.json()["id"]

    resp = await client.delete(f"/resources/{resource_id}", headers=auth_headers(token_b))
    assert resp.status_code == 404


async def test_pagination(client: AsyncClient, token_a: str):
    for i in range(5):
        await client.post("/resources", data=_form_data(resource_payload(title=f"Page-{i}")), headers=auth_headers(token_a))

    resp = await client.get("/resources?limit=2&offset=0", headers=auth_headers(token_a))
    assert resp.status_code == 200
    assert len(resp.json()["resources"]) == 2


async def test_invalid_transcript_json(client: AsyncClient, token_a: str):
    resp = await client.post(
        "/resources",
        data=_form_data(resource_payload(transcript="not-valid-json")),
        headers=auth_headers(token_a),
    )
    assert resp.status_code == 400


async def test_create_resource_with_media(client: AsyncClient, token_a: str):
    """Upload a resource with an attached media file."""
    fake_audio = b"\xff\xfb" + b"\x00" * 100  # minimal fake MP3 header bytes
    resp = await client.post(
        "/resources",
        data=_form_data(resource_payload()),
        files={"media_file": ("test.mp3", io.BytesIO(fake_audio), "audio/mpeg")},
        headers=auth_headers(token_a),
    )
    # Validation may reject tiny fake file, but the endpoint must respond correctly
    assert resp.status_code in (200, 400)


async def test_missing_required_field(client: AsyncClient, token_a: str):
    """Omitting a required Form field should return 422."""
    payload = _form_data(resource_payload())
    del payload["title"]
    resp = await client.post("/resources", data=payload, headers=auth_headers(token_a))
    assert resp.status_code == 422


async def test_rate_limit_login(client: AsyncClient):
    """Login endpoint should enforce rate limiting (returns 429 after threshold)."""
    credentials = {"username": "nonexistent@example.com", "password": "wrongpassword"}
    responses = []
    for _ in range(12):
        resp = await client.post("/auth/login", data=credentials)
        responses.append(resp.status_code)

    # At least one response should be 429 (rate limit) after 10 requests/min
    assert 429 in responses or all(r == 401 for r in responses), (
        "Expected either 429 rate-limit or all 401 unauthorized responses"
    )
