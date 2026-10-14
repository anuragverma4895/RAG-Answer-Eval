import io
import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from pypdf import PdfReader

from app.config import ALLOWED_EXTENSIONS, MAX_UPLOAD_MB
from app.services.chunking import chunk_text
from app.services.storage import create_document, delete_document, list_documents, update_document
from app.services.vector_store import add_chunks, delete_document as delete_vectors

router = APIRouter()
logger = logging.getLogger(__name__)
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024


def extract_pages(filename: str, data: bytes) -> list[tuple[int, str]]:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        try:
            reader = PdfReader(io.BytesIO(data), strict=False)
            if reader.is_encrypted:
                try:
                    if not reader.decrypt(""):
                        raise HTTPException(400, "This PDF is password-protected and cannot be indexed.")
                except HTTPException:
                    raise
                except Exception:
                    raise HTTPException(400, "This PDF is password-protected and cannot be indexed.")
            return [(i + 1, page.extract_text() or "") for i, page in enumerate(reader.pages)]
        except HTTPException:
            raise
        except Exception:
            logger.exception("PDF extraction failed")
            raise HTTPException(400, "Could not read this PDF. Check that it is a valid, readable PDF.")
    try:
        return [(1, data.decode("utf-8-sig"))]
    except UnicodeDecodeError:
        raise HTTPException(400, "This text file must use UTF-8 encoding.")


def _mark_failed(doc_id: str) -> None:
    try:
        delete_vectors(doc_id)
    except Exception:
        logger.exception("Could not clean partial vectors for failed document %s", doc_id)
    update_document(doc_id, 0, "failed")


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    original_name = Path((file.filename or "document").replace("\\", "/")).name
    ext = Path(original_name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        await file.close()
        raise HTTPException(400, "Unsupported file type. Use PDF, TXT or Markdown.")
    if not original_name.strip() or original_name in {".", ".."}:
        await file.close()
        raise HTTPException(400, "The uploaded file must have a valid filename.")

    try:
        data = await file.read(MAX_UPLOAD_BYTES + 1)
    finally:
        await file.close()

    if not data:
        raise HTTPException(400, "The uploaded file is empty.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, f"File is larger than {MAX_UPLOAD_MB} MB.")

    doc_id = str(uuid.uuid4())
    create_document(doc_id, original_name, ext.lstrip("."), len(data))
    try:
        pages = extract_pages(original_name, data)
        chunks = []
        for page_number, page_text in pages:
            for piece in chunk_text(page_text):
                chunks.append({
                    "id": f"{doc_id}:{len(chunks)}",
                    "document_id": doc_id,
                    "document_name": original_name,
                    "chunk_index": len(chunks),
                    "page_number": page_number,
                    "text": piece,
                })
        if not chunks:
            raise HTTPException(
                400,
                "No selectable text was found. Scanned PDFs need OCR before they can be indexed.",
            )

        add_chunks(chunks)
        update_document(doc_id, len(chunks), "indexed")
        document = next((item for item in list_documents() if item["id"] == doc_id), None)
        if document is None:
            raise RuntimeError("Indexed document metadata could not be loaded.")
        return {"message": "Document indexed successfully", "document": document}
    except HTTPException:
        _mark_failed(doc_id)
        raise
    except Exception:
        logger.exception("Document indexing failed for %s", original_name)
        _mark_failed(doc_id)
        raise HTTPException(500, "Document indexing failed. Check the backend logs for details.")


@router.get("")
def documents():
    return list_documents()


@router.delete("/{document_id}")
def remove_document(document_id: str):
    docs = list_documents()
    if not any(item["id"] == document_id for item in docs):
        raise HTTPException(404, "Document not found.")
    try:
        delete_vectors(document_id)
        delete_document(document_id)
    except Exception:
        logger.exception("Could not delete document %s", document_id)
        raise HTTPException(500, "Could not fully delete this document. Check the backend logs.")
    return {"message": "Document deleted"}
