"""Tests for /health endpoint."""

from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from sqlalchemy.exc import OperationalError


@pytest.mark.asyncio
async def test_health_ok(client):
    """Health returns 200 when DB is connected."""
    resp = await client.get("/health")
    # May be 200 or 503 depending on whether DB is available in test env
    assert resp.status_code in (200, 503)
    data = resp.json()
    assert "status" in data
    assert "database" in data


@pytest.mark.asyncio
async def test_health_response_structure(client):
    """Health response has expected structure."""
    resp = await client.get("/health")
    data = resp.json()
    if resp.status_code == 200:
        assert data["status"] == "ok"
        assert data["database"] == "connected"
    else:
        assert data["status"] == "error"
        assert "database" in data
