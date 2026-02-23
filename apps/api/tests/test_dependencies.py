"""Tests for limit validation dependencies."""

import pytest
from fastapi import HTTPException

from app.dependencies import (
    validate_pdf_size_mb,
    validate_page_count,
    validate_chunks_per_doc,
    validate_top_k,
    validate_completion_tokens,
)
from app.core.config import settings


def test_validate_pdf_size_mb_accepts_under_limit():
    assert validate_pdf_size_mb(5.0) == 5.0


def test_validate_pdf_size_mb_accepts_at_limit():
    assert validate_pdf_size_mb(settings.max_pdf_mb) == settings.max_pdf_mb


def test_validate_pdf_size_mb_rejects_over_limit():
    with pytest.raises(HTTPException) as exc_info:
        validate_pdf_size_mb(settings.max_pdf_mb + 1)
    assert exc_info.value.status_code == 400
    assert "max_mb" in str(exc_info.value.detail)


def test_validate_page_count_accepts_under_limit():
    assert validate_page_count(10) == 10


def test_validate_page_count_accepts_at_limit():
    assert validate_page_count(settings.max_pdf_pages) == settings.max_pdf_pages


def test_validate_page_count_rejects_over_limit():
    with pytest.raises(HTTPException) as exc_info:
        validate_page_count(settings.max_pdf_pages + 1)
    assert exc_info.value.status_code == 400


def test_validate_chunks_per_doc_accepts_under_limit():
    assert validate_chunks_per_doc(100) == 100


def test_validate_chunks_per_doc_accepts_at_limit():
    assert validate_chunks_per_doc(settings.max_chunks_per_doc) == settings.max_chunks_per_doc


def test_validate_chunks_per_doc_rejects_over_limit():
    with pytest.raises(Exception) as exc_info:
        validate_chunks_per_doc(settings.max_chunks_per_doc + 1)
    assert exc_info.value.status_code == 400


def test_validate_top_k_accepts_under_limit():
    assert validate_top_k(5) == 5


def test_validate_top_k_accepts_at_limit():
    assert validate_top_k(settings.top_k_max) == settings.top_k_max


def test_validate_top_k_rejects_over_limit():
    with pytest.raises(HTTPException) as exc_info:
        validate_top_k(settings.top_k_max + 1)
    assert exc_info.value.status_code == 400


def test_validate_completion_tokens_accepts_under_limit():
    assert validate_completion_tokens(100) == 100


def test_validate_completion_tokens_accepts_at_limit():
    assert validate_completion_tokens(settings.max_completion_tokens) == settings.max_completion_tokens


def test_validate_completion_tokens_rejects_over_limit():
    with pytest.raises(HTTPException) as exc_info:
        validate_completion_tokens(settings.max_completion_tokens + 1)
    assert exc_info.value.status_code == 400
