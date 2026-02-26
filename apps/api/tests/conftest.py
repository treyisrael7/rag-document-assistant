"""Pytest fixtures."""

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.core.rate_limit import clear_store


@pytest.fixture(scope="session")
def event_loop():
    """Use a single event loop for all async tests to avoid SQLAlchemy 'attached to different loop' errors."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


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
