import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routes.documents import router as documents_router
from app.routes.rag import router as rag_router
from app.routes.evaluations import router as evaluations_router
from app.routes.stats import router as stats_router
from app.services.storage import init_db

app = FastAPI(title="RAG Answer Eval API", version="1.1.0")

allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
configured_origin = os.getenv("FRONTEND_ORIGIN", "").strip().rstrip("/")
if configured_origin:
    allowed_origins.append(configured_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

init_db()
app.include_router(documents_router, prefix="/api/documents", tags=["Documents"])
app.include_router(rag_router, prefix="/api/rag", tags=["RAG"])
app.include_router(evaluations_router, prefix="/api/evaluations", tags=["Evaluations"])
app.include_router(stats_router, prefix="/api", tags=["Stats"])


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "rag-answer-eval"}


# In the Docker/Render deployment the built React app is served from this
# FastAPI process, so the browser and API share one origin and need no CORS
# workaround. In local development this directory is absent; Vite runs separately.
STATIC_DIR = Path(__file__).resolve().parents[1] / "static"
if STATIC_DIR.is_dir() and (STATIC_DIR / "index.html").is_file():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="frontend")
