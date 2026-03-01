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
    """POST /documents/{id}/ingest is rate limited to 3 per day."""
    monkeypatch.setattr(settings, "demo_key", None)
    monkeypatch.setattr(settings, "openai_api_key", "sk-test")
    monkeypatch.setattr(settings, "s3_bucket", None)

    user_id = "11111111-1111-1111-1111-111111111111"
    presign_body = {
        "user_id": user_id,
        "filename": "test.pdf",
        "content_type": "application/pdf",
        "file_size_bytes": 1024,
    }
    # Minimal valid PDF bytes for upload
    pdf_bytes = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    doc_ids = []
    for _ in range(4):
        pr = await client.post("/documents/presign", json=presign_body)
        assert pr.status_code == 200
        data = pr.json()
        doc_id = data["document_id"]
        doc_ids.append(doc_id)
        key = data["s3_key"]
        await client.put(f"/documents/upload-local?key={key}", content=pdf_bytes)
        await client.post(
            "/documents/confirm",
            json={"user_id": user_id, "document_id": doc_id, "s3_key": key},
        )

    for i in range(3):
        resp = await client.post(
            f"/documents/{doc_ids[i]}/ingest",
            json={"user_id": user_id},
        )
        assert resp.status_code == 200, f"Request {i+1}"

    resp = await client.post(
        f"/documents/{doc_ids[3]}/ingest",
        json={"user_id": user_id},
    )
    assert resp.status_code == 429
    assert resp.json()["limit"] == 3
    assert resp.json()["window"] == "day"


@pytest.mark.asyncio
async def test_presign_rate_limit(client, monkeypatch):
    """POST /documents/presign is rate limited to 10 per day."""
    monkeypatch.setattr(settings, "demo_key", None)
    monkeypatch.setattr(settings, "s3_bucket", None)  # Use LocalStorage
    presign_body = {
        "user_id": "11111111-1111-1111-1111-111111111111",
        "filename": "test.pdf",
        "content_type": "application/pdf",
        "file_size_bytes": 1024,
    }
    for _ in range(10):
        resp = await client.post("/documents/presign", json=presign_body)
        assert resp.status_code == 200

    resp = await client.post("/documents/presign", json=presign_body)
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
