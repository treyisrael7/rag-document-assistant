from fastapi import APIRouter

router = APIRouter(prefix="/ask", tags=["ask"])


@router.post("")
async def ask():
    """Placeholder for RAG Q&A. Rate limit: 10/hour."""
    return {"message": "ask endpoint placeholder"}
