from app.services import vector_store


class FakeCollection:
    def __init__(self, count, payload=None):
        self.count_value = count
        self.payload = payload or {}
        self.query_args = None

    def count(self):
        return self.count_value

    def query(self, **kwargs):
        self.query_args = kwargs
        return self.payload

    def delete(self, **kwargs):
        self.deleted_with = kwargs


def test_search_caps_requested_results_to_indexed_vector_count(monkeypatch):
    payload = {
        "ids": [["doc-1:0"]],
        "documents": [["Refunds are available within 30 days."]],
        "metadatas": [[{
            "document_name": "policy.txt",
            "document_id": "doc-1",
            "chunk_index": "0",
            "page_number": "1",
        }]],
        "distances": [[0.1]],
    }
    collection = FakeCollection(1, payload)
    monkeypatch.setattr(vector_store, "_collection", lambda: collection)
    monkeypatch.setattr(vector_store, "encode", lambda texts: [[0.0, 1.0]])

    result = vector_store.search("What is the refund policy?", top_k=10, threshold=0.5)

    assert collection.query_args["n_results"] == 1
    assert result == [{
        "id": "doc-1:0",
        "document_name": "policy.txt",
        "document_id": "doc-1",
        "chunk_index": 0,
        "page_number": 1,
        "similarity": 0.9,
        "text": "Refunds are available within 30 days.",
    }]


def test_search_returns_empty_when_no_vectors_are_indexed(monkeypatch):
    collection = FakeCollection(0)
    monkeypatch.setattr(vector_store, "_collection", lambda: collection)
    monkeypatch.setattr(
        vector_store,
        "encode",
        lambda texts: (_ for _ in ()).throw(AssertionError("No query embedding is needed")),
    )

    assert vector_store.search("A question?", top_k=5, threshold=0.25) == []
