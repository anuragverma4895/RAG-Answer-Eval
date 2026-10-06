from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.documents import router as documents_router
from app.routes.rag import router as rag_router
from app.routes.evaluations import router as evaluations_router
from app.routes.stats import router as stats_router
from app.services.storage import init_db

app = FastAPI(title="RAG Answer Eval API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()
app.include_router(documents_router, prefix="/api/documents", tags=["Documents"])
app.include_router(rag_router, prefix="/api/rag", tags=["RAG"])
app.include_router(evaluations_router, prefix="/api/evaluations", tags=["Evaluations"])
app.include_router(stats_router, prefix="/api", tags=["Stats"])

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "rag-answer-eval"}
