"""Document ingestion: PDF extraction, chunking, embeddings."""

import uuid

from sqlalchemy import delete, select

from app.core.config import settings
from app.models import Document, DocumentChunk
from app.services.storage import get_storage


def _extract_text_per_page(pdf_bytes: bytes) -> list[tuple[int, str]]:
    """Extract text per page using PyMuPDF. Returns [(page_number, text), ...]."""
    import fitz  # PyMuPDF

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        result = []
        for i in range(min(len(doc), settings.max_pdf_pages)):
            page = doc[i]
            text = page.get_text()
            result.append((i + 1, text))
        return result
    finally:
        doc.close()


def _is_word_char(c: str) -> bool:
    """True if char is alphanumeric or hyphen/underscore (part of a word)."""
    return c.isalnum() or c in "-_"


def _chunk_text(
    page_texts: list[tuple[int, str]],
) -> list[tuple[int, str]]:
    """
    Chunk text with configurable size and overlap, preferring word boundaries.
    Filters out tiny chunks (e.g. PDF footers like "Page 2 of 2").
    Returns [(page_number, chunk_text), ...]
    """
    chunk_size = settings.chunk_size
    overlap = settings.chunk_overlap
    min_chars = settings.min_chunk_chars
    step = max(1, chunk_size - overlap)

    chunks: list[tuple[int, str]] = []
    for page_num, text in page_texts:
        text = text.strip()
        if not text:
            continue
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))

            # Prefer word boundary at end: avoid cutting mid-word
            if end < len(text) and _is_word_char(text[end]):
                last_space = text.rfind(" ", start, end)
                if last_space > start:
                    end = last_space + 1

            # If we're starting mid-word, back up to include the whole word (only if we find a space)
            if start > 0 and _is_word_char(text[start - 1]):
                prev_space = text.rfind(" ", 0, start)
                if prev_space >= 0:
                    start = prev_space + 1
                    if start >= end:
                        start += step
                        continue

            chunk = text[start:end].strip()
            if chunk and len(chunk) >= min_chars:
                chunks.append((page_num, chunk))
            start += step

    return chunks[: settings.max_chunks_per_doc]


def _create_embeddings(texts: list[str]) -> list[list[float]]:
    """Create embeddings via OpenAI API. Returns list of embedding vectors."""
    from openai import OpenAI

    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is not configured")

    client = OpenAI(api_key=settings.openai_api_key)

    # text-embedding-3 models support dimensions param; older models do not
    create_kwargs: dict = {
        "input": texts,
        "model": settings.openai_embedding_model,
    }
    if settings.openai_embedding_model.startswith("text-embedding-3"):
        create_kwargs["dimensions"] = settings.openai_embedding_dim
    response = client.embeddings.create(**create_kwargs)

    # Preserve order; response.data is in order of input
    by_index = {item.index: item.embedding for item in response.data}
    return [by_index[i] for i in range(len(texts))]


async def run_ingestion(document_id: uuid.UUID) -> None:
    """
    Background ingestion: download PDF, extract, chunk, embed, store.
    On success: update document page_count and status=ready.
    On failure: update status=failed and error_message.
    """
    from app.db.base import async_session_maker

    async with async_session_maker() as db:
        try:
            result = await db.execute(
                select(Document).where(Document.id == document_id)
            )
            doc = result.scalar_one_or_none()
            if not doc:
                return

            storage = get_storage()
            pdf_bytes = storage.download(doc.s3_key)

            page_texts = _extract_text_per_page(pdf_bytes)
            if not page_texts:
                doc.status = "failed"
                doc.error_message = "No text extracted from PDF"
                await db.commit()
                return

            chunks_with_pages = _chunk_text(page_texts)
            if not chunks_with_pages:
                doc.status = "failed"
                doc.error_message = "No chunks produced after extraction"
                await db.commit()
                return

            texts = [c[1] for c in chunks_with_pages]
            embeddings = _create_embeddings(texts)

            # Delete existing chunks for this document (re-ingestion)
            await db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))

            for i, ((page_num, content), embedding) in enumerate(
                zip(chunks_with_pages, embeddings)
            ):
                chunk = DocumentChunk(
                    document_id=document_id,
                    chunk_index=i,
                    content=content,
                    page_number=page_num,
                    embedding=embedding,
                )
                db.add(chunk)

            doc.page_count = len(page_texts)
            doc.status = "ready"
            doc.error_message = None
            await db.commit()

        except Exception as e:
            await db.rollback()
            # Use fresh session to persist failure status
            async with async_session_maker() as db2:
                result = await db2.execute(
                    select(Document).where(Document.id == document_id)
                )
                doc = result.scalar_one_or_none()
                if doc:
                    doc.status = "failed"
                    doc.error_message = str(e)[:2000]  # Cap error length
                await db2.commit()
