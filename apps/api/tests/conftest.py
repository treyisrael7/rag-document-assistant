"""Pytest fixtures."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.core.rate_limit import clear_store


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.fixture(autouse=True)
def reset_rate_limit():
    """Clear rate limit store before each test."""
    clear_store()
    yield
    clear_store()
