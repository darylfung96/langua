"""Tests for the /lyrics endpoints, including per-user isolation."""
import pytest
from httpx import AsyncClient

from tests.conftest import auth_headers, lyric_payload

pytestmark = pytest.mark.asyncio


async def test_create_lyric(client: AsyncClient, token_a: str):
    resp = await client.post("/lyrics", json=lyric_payload(), headers=auth_headers(token_a))
    assert resp.status_code == 200
    assert resp.json()["title"] == "Test Song"


async def test_list_lyrics(client: AsyncClient, token_a: str):
    await client.post("/lyrics", json=lyric_payload(title="L1"), headers=auth_headers(token_a))
    await client.post("/lyrics", json=lyric_payload(title="L2"), headers=auth_headers(token_a))

    resp = await client.get("/lyrics", headers=auth_headers(token_a))
    assert resp.status_code == 200
    titles = [l["title"] for l in resp.json()["lyrics"]]
    assert "L1" in titles and "L2" in titles


async def test_get_lyric_by_id(client: AsyncClient, token_a: str):
    create = await client.post("/lyrics", json=lyric_payload(), headers=auth_headers(token_a))
    lyric_id = create.json()["id"]

    resp = await client.get(f"/lyrics/{lyric_id}", headers=auth_headers(token_a))
    assert resp.status_code == 200
    assert resp.json()["id"] == lyric_id


async def test_delete_lyric(client: AsyncClient, token_a: str):
    create = await client.post("/lyrics", json=lyric_payload(), headers=auth_headers(token_a))
    lyric_id = create.json()["id"]

    resp = await client.delete(f"/lyrics/{lyric_id}", headers=auth_headers(token_a))
    assert resp.status_code == 200

    resp = await client.get(f"/lyrics/{lyric_id}", headers=auth_headers(token_a))
    assert resp.status_code == 404


async def test_user_isolation(client: AsyncClient, token_a: str, token_b: str):
    create = await client.post("/lyrics", json=lyric_payload(title="A-lyric"), headers=auth_headers(token_a))
    lyric_id = create.json()["id"]

    # B cannot see A's lyric in list
    resp = await client.get("/lyrics", headers=auth_headers(token_b))
    titles = [l["title"] for l in resp.json()["lyrics"]]
    assert "A-lyric" not in titles

    # B cannot fetch by id
    resp = await client.get(f"/lyrics/{lyric_id}", headers=auth_headers(token_b))
    assert resp.status_code == 404

    # B cannot delete
    resp = await client.delete(f"/lyrics/{lyric_id}", headers=auth_headers(token_b))
    assert resp.status_code == 404


async def test_invalid_transcript_json(client: AsyncClient, token_a: str):
    resp = await client.post(
        "/lyrics",
        json=lyric_payload(transcript="not-json"),
        headers=auth_headers(token_a),
    )
    assert resp.status_code == 400
