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

from fastapi.testclient import TestClient

import app.services.storage as storage
from app.main import app
from app.routes import documents as documents_route

client = TestClient(app)


def test_upload_list_and_delete_text_document(monkeypatch, tmp_path):
    monkeypatch.setattr(storage, "SQLITE_PATH", str(tmp_path / "test.db"))
    storage.init_db()

    indexed_chunks = []
    monkeypatch.setattr(documents_route, "add_chunks", lambda chunks: indexed_chunks.extend(chunks))
    monkeypatch.setattr(documents_route, "delete_vectors", lambda document_id: None)

    upload = client.post(
        "/api/documents/upload",
        files={"file": ("facts.txt", b"Refunds are available within 30 days.", "text/plain")},
    )
    assert upload.status_code == 200
    document = upload.json()["document"]
    assert document["status"] == "indexed"
    assert document["chunks"] == 1
    assert indexed_chunks[0]["text"] == "Refunds are available within 30 days."

    listed = client.get("/api/documents")
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [document["id"]]

    deleted = client.delete(f"/api/documents/{document['id']}")
    assert deleted.status_code == 200
    assert client.get("/api/documents").json() == []
