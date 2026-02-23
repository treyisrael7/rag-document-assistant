"""Tests for basic route responses."""

import pytest

from app.core.config import settings


@pytest.mark.asyncio
async def test_root(client):
    """Root returns API message."""
    resp = await client.get("/")
    assert resp.status_code == 200
    assert "message" in resp.json()


@pytest.mark.asyncio
async def test_ask_placeholder(client, monkeypatch):
    """Ask returns placeholder (when DEMO_KEY not set or key provided)."""
    monkeypatch.setattr(settings, "demo_key", None)  # ensure no gate
    resp = await client.post("/ask", json={})
    assert resp.status_code == 200
    assert resp.json().get("message") == "ask endpoint placeholder"


@pytest.mark.asyncio
async def test_ingest_placeholder(client, monkeypatch):
    """Ingest returns placeholder."""
    monkeypatch.setattr(settings, "demo_key", None)
    resp = await client.post("/documents/ingest", json={})
    assert resp.status_code == 200
    assert "message" in resp.json()


@pytest.mark.asyncio
async def test_presign_placeholder(client, monkeypatch):
    """Presign returns placeholder."""
    monkeypatch.setattr(settings, "demo_key", None)
    resp = await client.post("/documents/presign", json={})
    assert resp.status_code == 200
    assert "message" in resp.json()
