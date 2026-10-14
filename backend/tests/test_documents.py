import pytest
from fastapi import HTTPException

from app.routes.documents import extract_pages


def test_extracts_utf8_text_and_removes_bom():
    pages = extract_pages("notes.txt", b"\xef\xbb\xbfRefunds are available within 30 days.")
    assert pages == [(1, "Refunds are available within 30 days.")]


def test_rejects_non_utf8_text():
    with pytest.raises(HTTPException) as exc_info:
        extract_pages("notes.txt", b"\xff\xfe\xfa")

    assert exc_info.value.status_code == 400
    assert "UTF-8" in exc_info.value.detail


def test_rejects_unreadable_pdf():
    with pytest.raises(HTTPException) as exc_info:
        extract_pages("broken.pdf", b"This is not a PDF document")

    assert exc_info.value.status_code == 400
    assert "valid, readable PDF" in exc_info.value.detail
