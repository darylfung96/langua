"""Tests for the /visuals endpoints, including per-user isolation."""
import pytest
from httpx import AsyncClient

from tests.conftest import auth_headers, visual_payload

pytestmark = pytest.mark.asyncio


async def test_create_visual(client: AsyncClient, token_a: str):
    resp = await client.post("/visuals", json=visual_payload(), headers=auth_headers(token_a))
    assert resp.status_code == 200
    assert resp.json()["word"] == "neko"


async def test_list_visuals(client: AsyncClient, token_a: str):
    await client.post("/visuals", json=visual_payload(word="inu"), headers=auth_headers(token_a))
    await client.post("/visuals", json=visual_payload(word="neko"), headers=auth_headers(token_a))

    resp = await client.get("/visuals", headers=auth_headers(token_a))
    assert resp.status_code == 200
    words = [v["word"] for v in resp.json()["visuals"]]
    assert "inu" in words and "neko" in words


async def test_get_visual_by_id(client: AsyncClient, token_a: str):
    create = await client.post("/visuals", json=visual_payload(), headers=auth_headers(token_a))
    visual_id = create.json()["id"]

    resp = await client.get(f"/visuals/{visual_id}", headers=auth_headers(token_a))
    assert resp.status_code == 200
    assert resp.json()["id"] == visual_id


async def test_delete_visual(client: AsyncClient, token_a: str):
    create = await client.post("/visuals", json=visual_payload(), headers=auth_headers(token_a))
    visual_id = create.json()["id"]

    resp = await client.delete(f"/visuals/{visual_id}", headers=auth_headers(token_a))
    assert resp.status_code == 200

    resp = await client.get(f"/visuals/{visual_id}", headers=auth_headers(token_a))
    assert resp.status_code == 404


async def test_user_isolation(client: AsyncClient, token_a: str, token_b: str):
    create = await client.post("/visuals", json=visual_payload(word="tori"), headers=auth_headers(token_a))
    visual_id = create.json()["id"]

    resp = await client.get("/visuals", headers=auth_headers(token_b))
    words = [v["word"] for v in resp.json()["visuals"]]
    assert "tori" not in words

    resp = await client.get(f"/visuals/{visual_id}", headers=auth_headers(token_b))
    assert resp.status_code == 404

    resp = await client.delete(f"/visuals/{visual_id}", headers=auth_headers(token_b))
    assert resp.status_code == 404


async def test_invalid_images_json(client: AsyncClient, token_a: str):
    resp = await client.post(
        "/visuals",
        json=visual_payload(images="not-json"),
        headers=auth_headers(token_a),
    )
    assert resp.status_code == 400
