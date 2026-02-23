"""Tests for rate limit middleware."""

import pytest

from app.core.config import settings


@pytest.mark.asyncio
async def test_ask_rate_limit(client, monkeypatch):
    """POST /ask is rate limited to 10 per hour."""
    monkeypatch.setattr(settings, "demo_key", None)
    for i in range(10):
        resp = await client.post("/ask", json={})
        assert resp.status_code == 200, f"Request {i+1} should succeed"

    resp = await client.post("/ask", json={})
    assert resp.status_code == 429
    data = resp.json()
    assert data["detail"] == "Rate limit exceeded"
    assert "retry_after_seconds" in data
    assert data["limit"] == 10
    assert data["window"] == "hour"
    assert "Retry-After" in resp.headers


@pytest.mark.asyncio
async def test_ingest_rate_limit(client, monkeypatch):
    """POST /documents/ingest is rate limited to 3 per day."""
    monkeypatch.setattr(settings, "demo_key", None)
    for _ in range(3):
        resp = await client.post("/documents/ingest", json={})
        assert resp.status_code == 200

    resp = await client.post("/documents/ingest", json={})
    assert resp.status_code == 429
    assert resp.json()["limit"] == 3
    assert resp.json()["window"] == "day"


@pytest.mark.asyncio
async def test_presign_rate_limit(client, monkeypatch):
    """POST /documents/presign is rate limited to 10 per day."""
    monkeypatch.setattr(settings, "demo_key", None)
    for _ in range(10):
        resp = await client.post("/documents/presign", json={})
        assert resp.status_code == 200

    resp = await client.post("/documents/presign", json={})
    assert resp.status_code == 429
    assert resp.json()["limit"] == 10
    assert resp.json()["window"] == "day"


@pytest.mark.asyncio
async def test_non_rate_limited_paths(client, monkeypatch):
    """GET / and /health are not rate limited."""
    monkeypatch.setattr(settings, "demo_key", None)
    for _ in range(15):
        resp = await client.get("/")
        assert resp.status_code == 200
        resp = await client.get("/health")
        assert resp.status_code in (200, 503)


@pytest.mark.asyncio
async def test_different_users_separate_limits(client, monkeypatch):
    """Different x-user-id get separate rate limits."""
    monkeypatch.setattr(settings, "demo_key", None)
    for _ in range(10):
        resp = await client.post(
            "/ask", json={}, headers={"x-user-id": "user-a"}
        )
        assert resp.status_code == 200

    # user-a is limited
    resp = await client.post("/ask", json={}, headers={"x-user-id": "user-a"})
    assert resp.status_code == 429

    # user-b still has quota
    resp = await client.post("/ask", json={}, headers={"x-user-id": "user-b"})
    assert resp.status_code == 200
