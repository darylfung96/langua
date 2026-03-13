"""Tests for the /stories endpoints, including per-user isolation."""
import pytest
from httpx import AsyncClient

from tests.conftest import auth_headers, story_payload

pytestmark = pytest.mark.asyncio


async def test_create_story(client: AsyncClient, token_a: str):
    resp = await client.post("/stories", json=story_payload(), headers=auth_headers(token_a))
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "El Gato"
    assert "id" in data


async def test_list_stories(client: AsyncClient, token_a: str):
    await client.post("/stories", json=story_payload(title="S1"), headers=auth_headers(token_a))
    await client.post("/stories", json=story_payload(title="S2"), headers=auth_headers(token_a))

    resp = await client.get("/stories", headers=auth_headers(token_a))
    assert resp.status_code == 200
    titles = [s["title"] for s in resp.json()["stories"]]
    assert "S1" in titles
    assert "S2" in titles


async def test_get_story_by_id(client: AsyncClient, token_a: str):
    create = await client.post("/stories", json=story_payload(), headers=auth_headers(token_a))
    story_id = create.json()["id"]

    resp = await client.get(f"/stories/{story_id}", headers=auth_headers(token_a))
    assert resp.status_code == 200
    assert resp.json()["id"] == story_id


async def test_delete_story(client: AsyncClient, token_a: str):
    create = await client.post("/stories", json=story_payload(), headers=auth_headers(token_a))
    story_id = create.json()["id"]

    resp = await client.delete(f"/stories/{story_id}", headers=auth_headers(token_a))
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    resp = await client.get(f"/stories/{story_id}", headers=auth_headers(token_a))
    assert resp.status_code == 404


async def test_user_isolation_list(client: AsyncClient, token_a: str, token_b: str):
    """User A's stories must not appear in User B's list."""
    await client.post("/stories", json=story_payload(title="A-only"), headers=auth_headers(token_a))

    resp_b = await client.get("/stories", headers=auth_headers(token_b))
    titles_b = [s["title"] for s in resp_b.json()["stories"]]
    assert "A-only" not in titles_b


async def test_user_isolation_get(client: AsyncClient, token_a: str, token_b: str):
    """User B cannot fetch User A's story by ID."""
    create = await client.post("/stories", json=story_payload(), headers=auth_headers(token_a))
    story_id = create.json()["id"]

    resp = await client.get(f"/stories/{story_id}", headers=auth_headers(token_b))
    assert resp.status_code == 404


async def test_user_isolation_delete(client: AsyncClient, token_a: str, token_b: str):
    """User B cannot delete User A's story."""
    create = await client.post("/stories", json=story_payload(), headers=auth_headers(token_a))
    story_id = create.json()["id"]

    resp = await client.delete(f"/stories/{story_id}", headers=auth_headers(token_b))
    assert resp.status_code == 404


async def test_pagination(client: AsyncClient, token_a: str):
    for i in range(5):
        await client.post("/stories", json=story_payload(title=f"Page-{i}"), headers=auth_headers(token_a))

    resp = await client.get("/stories?limit=2&offset=0", headers=auth_headers(token_a))
    assert resp.status_code == 200
    assert len(resp.json()["stories"]) == 2


async def test_invalid_vocabulary_json(client: AsyncClient, token_a: str):
    resp = await client.post(
        "/stories",
        json=story_payload(vocabulary="not-valid-json"),
        headers=auth_headers(token_a),
    )
    assert resp.status_code == 400
