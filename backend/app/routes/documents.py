import io
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from pypdf import PdfReader
from app.config import ALLOWED_EXTENSIONS, MAX_UPLOAD_MB
from app.services.storage import create_document, update_document, list_documents, delete_document
from app.services.chunking import chunk_text
from app.services.vector_store import add_chunks, delete_document as delete_vectors

router=APIRouter()

def extract_pages(filename, data):
    ext=Path(filename).suffix.lower()
    if ext==".pdf":
        try:
            reader=PdfReader(io.BytesIO(data))
            return [(i+1,(page.extract_text() or "")) for i,page in enumerate(reader.pages)]
        except Exception as exc:
            raise HTTPException(400,f"Could not read PDF: {exc}")
    try:
        return [(1,data.decode("utf-8",errors="replace"))]
    except Exception:
        raise HTTPException(400,"Could not decode the document as UTF-8 text.")

@router.post("/upload")
async def upload_document(file: UploadFile=File(...)):
    filename=file.filename or "document"
    ext=Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400,"Unsupported file type. Use PDF, TXT or Markdown.")
    data=await file.read()
    if len(data)>MAX_UPLOAD_MB*1024*1024:
        raise HTTPException(413,f"File is larger than {MAX_UPLOAD_MB} MB.")
    doc_id=str(uuid.uuid4())
    create_document(doc_id,filename,ext.lstrip("."),len(data))
    try:
        pages=extract_pages(filename,data)
        chunks=[]
        for page_number,text in pages:
            pieces=chunk_text(text)
            for idx,piece in enumerate(pieces):
                chunks.append({
                    "id":f"{doc_id}:{len(chunks)}",
                    "document_id":doc_id,
                    "document_name":filename,
                    "chunk_index":len(chunks),
                    "page_number":page_number,
                    "text":piece
                })
        if not chunks:
            update_document(doc_id,0,"failed")
            raise HTTPException(400,"The document contains no extractable text.")
        add_chunks(chunks)
        update_document(doc_id,len(chunks),"indexed")
        return {"message":"Document indexed successfully","document":next(d for d in list_documents() if d["id"]==doc_id)}
    except HTTPException:
        raise
    except Exception as exc:
        update_document(doc_id,0,"failed")
        raise HTTPException(500,f"Document indexing failed: {exc}")

@router.get("")
def documents():
    return list_documents()

@router.delete("/{document_id}")
def remove_document(document_id:str):
    docs=list_documents()
    if not any(d["id"]==document_id for d in docs):
        raise HTTPException(404,"Document not found.")
    delete_vectors(document_id)
    delete_document(document_id)
    return {"message":"Document deleted"}
