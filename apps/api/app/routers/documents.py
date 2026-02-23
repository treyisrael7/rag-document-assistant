from fastapi import APIRouter

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/ingest")
async def ingest():
    """Placeholder for document ingestion. Rate limit: 3/day."""
    return {"message": "ingest endpoint placeholder"}


@router.post("/presign")
async def presign():
    """Placeholder for presigned upload URL. Rate limit: 10/day."""
    return {"message": "presign endpoint placeholder"}
