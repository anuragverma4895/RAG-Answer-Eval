import logging
import time

from fastapi import APIRouter, HTTPException

from app.config import GEMINI_MODEL, TOP_K
from app.schemas import QueryRequest
from app.services.llm import evaluate, generate_answer
from app.services.storage import create_evaluation
from app.services.vector_store import search

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/query")
def query_rag(request: QueryRequest):
    started = time.perf_counter()
    try:
        retrieved = search(
            request.question,
            request.top_k or TOP_K,
            request.similarity_threshold,
        )
    except RuntimeError as exc:
        logger.exception("Retrieval could not be completed")
        raise HTTPException(503, str(exc))
    except Exception:
        logger.exception("Retrieval failed")
        raise HTTPException(502, "Retrieval failed. Check the backend logs and try again.")

    if not retrieved:
        raise HTTPException(
            404,
            "No sufficiently relevant information was found. Upload a document or lower the similarity threshold.",
        )

    context = "\n\n".join(
        f"[Source {i + 1} | {chunk['document_name']} | page {chunk['page_number'] or 'n/a'}]\n{chunk['text']}"
        for i, chunk in enumerate(retrieved)
    )
    try:
        answer = generate_answer(request.question, context)
        evaluation = evaluate(request.question, answer, context)
    except RuntimeError as exc:
        raise HTTPException(503, str(exc))
    except Exception:
        logger.exception("Gemini generation/evaluation failed")
        raise HTTPException(502, "The AI pipeline failed. Check your Gemini configuration and backend logs.")

    latency = round((time.perf_counter() - started) * 1000)
    # Save source text along with metadata so older pipeline runs can be
    # inspected from the Runs page without relying on the in-memory response.
    saved_sources = [
        {
            "id": chunk.get("id", ""),
            "document_name": chunk["document_name"],
            "document_id": chunk["document_id"],
            "chunk_index": chunk["chunk_index"],
            "page_number": chunk["page_number"],
            "similarity": chunk["similarity"],
            "text": chunk["text"],
        }
        for chunk in retrieved
    ]
    try:
        eval_id = create_evaluation(
            request.question,
            answer,
            saved_sources,
            evaluation,
            latency,
            GEMINI_MODEL,
        )
    except Exception:
        logger.exception("Could not persist evaluation result")
        raise HTTPException(500, "The answer was generated but its evaluation could not be saved.")

    return {
        "evaluation_id": eval_id,
        "question": request.question,
        "answer": answer,
        "model": GEMINI_MODEL,
        "latency_ms": latency,
        "retrieved_context": retrieved,
        "evaluation": evaluation,
    }
