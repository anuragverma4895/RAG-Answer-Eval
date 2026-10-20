from fastapi.testclient import TestClient

from app.main import app
from app.routes import rag as rag_route

client = TestClient(app)


def test_query_uses_controls_and_saves_source_text(monkeypatch):
    source_text = "Refunds are available within 30 days of purchase."
    retrieved = [
        {
            "id": "doc-1:0",
            "document_name": "refund-policy.txt",
            "document_id": "doc-1",
            "chunk_index": 0,
            "page_number": 1,
            "similarity": 0.91,
            "text": source_text,
        }
    ]
    captured = {}
    evaluation = {
        "answer_relevance": 95,
        "faithfulness": 98,
        "context_precision": 91,
        "completeness": 90,
        "overall_score": 94,
        "verdict": "Excellent",
        "reasoning": "The answer is fully supported by the source.",
        "issues": [],
    }

    def fake_search(question, top_k, threshold):
        captured["search"] = (question, top_k, threshold)
        return retrieved

    def fake_create_evaluation(question, answer, saved_sources, scores, latency, model):
        captured["saved_sources"] = saved_sources
        captured["saved_answer"] = answer
        return 42

    monkeypatch.setattr(rag_route, "search", fake_search)
    monkeypatch.setattr(rag_route, "generate_answer", lambda question, context: "Refunds are available within 30 days.")
    monkeypatch.setattr(rag_route, "evaluate", lambda question, answer, context: evaluation)
    monkeypatch.setattr(rag_route, "create_evaluation", fake_create_evaluation)

    response = client.post(
        "/api/rag/query",
        json={
            "question": "What is the refund policy?",
            "top_k": 3,
            "similarity_threshold": 0.4,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["evaluation_id"] == 42
    assert payload["evaluation"]["overall_score"] == 94
    assert payload["retrieved_context"][0]["text"] == source_text
    assert captured["search"] == ("What is the refund policy?", 3, 0.4)
    assert captured["saved_sources"][0]["text"] == source_text
    assert captured["saved_sources"][0]["document_name"] == "refund-policy.txt"
    assert captured["saved_answer"] == "Refunds are available within 30 days."
