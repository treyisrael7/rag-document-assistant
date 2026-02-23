"""Reusable dependencies for hard limits validation."""

from fastapi import HTTPException

from app.core.config import settings


def validate_pdf_size_mb(mb: float) -> float:
    if mb > settings.max_pdf_mb:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "PDF too large",
                "max_mb": settings.max_pdf_mb,
                "received_mb": round(mb, 2),
            },
        )
    return mb


def validate_page_count(pages: int) -> int:
    if pages > settings.max_pdf_pages:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Too many pages",
                "max_pages": settings.max_pdf_pages,
                "received_pages": pages,
            },
        )
    return pages


def validate_chunks_per_doc(count: int) -> int:
    if count > settings.max_chunks_per_doc:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Too many chunks",
                "max_chunks": settings.max_chunks_per_doc,
                "received_chunks": count,
            },
        )
    return count


def validate_top_k(top_k: int) -> int:
    if top_k > settings.top_k_max:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "top_k exceeds limit",
                "max_top_k": settings.top_k_max,
                "received": top_k,
            },
        )
    return top_k


def validate_completion_tokens(tokens: int) -> int:
    if tokens > settings.max_completion_tokens:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "completion_tokens exceeds limit",
                "max_tokens": settings.max_completion_tokens,
                "received": tokens,
            },
        )
    return tokens
