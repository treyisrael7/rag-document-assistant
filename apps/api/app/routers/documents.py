import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models import Document, User
from app.services.ingestion import run_ingestion
from app.services.storage import get_storage

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_CONTENT_TYPE = "application/pdf"


class PresignInput(BaseModel):
    user_id: uuid.UUID
    filename: str = Field(..., min_length=1)
    content_type: str = Field(..., pattern=r"^application/pdf$")
    file_size_bytes: int = Field(..., gt=0)


class PresignOutput(BaseModel):
    document_id: uuid.UUID
    s3_key: str
    upload_url: str
    method: str = "PUT"


class ConfirmInput(BaseModel):
    user_id: uuid.UUID
    document_id: uuid.UUID
    s3_key: str = Field(..., min_length=1)


def _mb_from_bytes(b: int) -> float:
    return b / (1024 * 1024)


def _validate_pdf_size(file_size_bytes: int) -> None:
    mb = _mb_from_bytes(file_size_bytes)
    if mb > settings.max_pdf_mb:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "PDF too large",
                "max_mb": settings.max_pdf_mb,
                "received_mb": round(mb, 2),
            },
        )


def _make_s3_key(user_id: uuid.UUID, document_id: uuid.UUID, filename: str) -> str:
    import re
    safe_name = re.sub(r"[^\w\.\-]", "_", filename)
    return f"documents/{user_id}/{document_id}/{safe_name}"


@router.post("/presign", response_model=PresignOutput)
async def presign(
    body: PresignInput,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Get presigned PUT URL for PDF upload. Rate limit: 10/day."""
    _validate_pdf_size(body.file_size_bytes)

    # Ensure user exists (create if not, for demo flow)
    result = await db.execute(select(User).where(User.id == body.user_id))
    user = result.scalar_one_or_none()
    if not user:
        user = User(id=body.user_id, email=f"{body.user_id}@temp.local")
        db.add(user)
        await db.flush()

    doc = Document(
        user_id=body.user_id,
        filename=body.filename,
        s3_key="",  # Set below
        status="pending",
    )
    db.add(doc)
    await db.flush()

    s3_key = _make_s3_key(body.user_id, doc.id, body.filename)
    doc.s3_key = s3_key

    storage = get_storage()
    upload_url, method = storage.generate_presigned_put(
        key=s3_key,
        content_type=body.content_type,
    )

    # For local storage, upload_url is relative; prepend base URL
    if upload_url.startswith("/"):
        base = str(request.base_url).rstrip("/")
        upload_url = f"{base}{upload_url}"

    return PresignOutput(
        document_id=doc.id,
        s3_key=s3_key,
        upload_url=upload_url,
        method=method,
    )


@router.post("/confirm")
async def confirm(
    body: ConfirmInput,
    db: AsyncSession = Depends(get_db),
):
    """Verify document exists in storage and set status=uploaded."""
    result = await db.execute(
        select(Document).where(
            Document.id == body.document_id,
            Document.user_id == body.user_id,
            Document.s3_key == body.s3_key,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    storage = get_storage()
    if not storage.exists(body.s3_key):
        raise HTTPException(
            status_code=400,
            detail="File not found in storage; upload may have failed",
        )

    doc.status = "uploaded"
    return {"status": "uploaded", "document_id": str(doc.id)}


@router.put("/upload-local")
async def upload_local(key: str, request: Request):
    """Local dev only: receive PUT file. Used when S3 is not configured."""
    from pathlib import Path

    from app.services.storage import get_storage, LocalStorage

    storage = get_storage()
    if not isinstance(storage, LocalStorage):
        raise HTTPException(status_code=400, detail="Local upload not available; use S3")

    path = Path(storage.get_path(key))
    path.parent.mkdir(parents=True, exist_ok=True)
    body = await request.body()
    path.write_bytes(body)
    return PlainTextResponse("OK", status_code=200)


class IngestInput(BaseModel):
    user_id: uuid.UUID


@router.post("/{document_id}/ingest")
async def ingest(
    document_id: uuid.UUID,
    body: IngestInput,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Start document ingestion. Rate limit: 3/day.
    Checks: doc ownership, status must be uploaded.
    Sets status=processing and runs ingestion in background.
    """
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == body.user_id,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.status != "uploaded":
        raise HTTPException(
            status_code=400,
            detail=f"Document must be uploaded to ingest; current status: {doc.status}",
        )

    if not settings.openai_api_key:
        raise HTTPException(
            status_code=503,
            detail="OpenAI API not configured; set OPENAI_API_KEY",
        )

    doc.status = "processing"
    doc.error_message = None
    await db.commit()

    background_tasks.add_task(run_ingestion, document_id)

    return {"status": "processing", "document_id": str(document_id)}
