from fastapi.testclient import TestClient

from app.main import app
from app.config import SIMILARITY_THRESHOLD, TOP_K
from app.schemas import QueryRequest

client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_rejects_unsupported_upload_type():
    response = client.post(
        "/api/documents/upload",
        files={"file": ("payload.exe", b"not a supported document", "application/octet-stream")},
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_rejects_blank_question_before_retrieval():
    response = client.post(
        "/api/rag/query",
        json={"question": "   ", "top_k": 5, "similarity_threshold": 0.25},
    )
    assert response.status_code == 422

def test_query_uses_configured_retrieval_defaults():
    request = QueryRequest(question="What is the policy?")
    assert request.top_k == TOP_K
    assert request.similarity_threshold == SIMILARITY_THRESHOLD

