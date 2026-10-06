import time
from fastapi import APIRouter, HTTPException
from app.schemas import QueryRequest
from app.config import GEMINI_MODEL, TOP_K, SIMILARITY_THRESHOLD
from app.services.vector_store import search
from app.services.llm import generate_answer, evaluate
from app.services.storage import create_evaluation

router=APIRouter()

@router.post("/query")
def query_rag(request:QueryRequest):
    started=time.perf_counter()
    top_k=request.top_k or TOP_K
    threshold=request.similarity_threshold
    retrieved=search(request.question,top_k,threshold)
    if not retrieved:
        raise HTTPException(404,"No sufficiently relevant information was found in the knowledge base. Upload a document or lower the similarity threshold.")
    context="\n\n".join([f"[Source {i+1} | {c['document_name']} | page {c['page_number'] or 'n/a'}]\n{c['text']}" for i,c in enumerate(retrieved)])
    try:
        answer=generate_answer(request.question,context)
        evaluation=evaluate(request.question,answer,context)
    except RuntimeError as exc:
        raise HTTPException(503,str(exc))
    except Exception as exc:
        raise HTTPException(502,f"AI pipeline failed: {exc}")
    latency=round((time.perf_counter()-started)*1000)
    eval_id=create_evaluation(
        request.question,answer,
        [{"document_name":c["document_name"],"document_id":c["document_id"],"chunk_index":c["chunk_index"],"page_number":c["page_number"],"similarity":c["similarity"]} for c in retrieved],
        evaluation,latency,GEMINI_MODEL
    )
    return {"evaluation_id":eval_id,"question":request.question,"answer":answer,"model":GEMINI_MODEL,"latency_ms":latency,
            "retrieved_context":retrieved,"evaluation":evaluation}
