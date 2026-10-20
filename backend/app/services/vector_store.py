from functools import lru_cache

from app.config import VECTOR_DB_PATH
from app.services.embeddings import encode


@lru_cache(maxsize=1)
def _collection():
    # ChromaDB initialization is deferred so FastAPI can bind to Render's
    # PORT and pass its health check before vector search is first required.
    import chromadb

    client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
    return client.get_or_create_collection(
        name="rag_answer_eval",
        metadata={"hnsw:space": "cosine"},
    )


def add_chunks(chunks):
    if not chunks:
        return

    collection = _collection()
    texts = [chunk["text"] for chunk in chunks]
    collection.add(
        ids=[chunk["id"] for chunk in chunks],
        documents=texts,
        metadatas=[
            {key: str(value) for key, value in chunk.items() if key not in ("id", "text")}
            for chunk in chunks
        ],
        embeddings=encode(texts),
    )


def search(query, top_k, threshold):
    collection = _collection()
    available = collection.count()
    if available == 0:
        return []

    # Request no more results than there are indexed vectors. This allows
    # users to ask for 5 or 10 chunks even when a new knowledge base has only
    # one or two chunks, without triggering a vector-store query error.
    result_count = min(max(1, int(top_k)), available)
    result = collection.query(
        query_embeddings=encode([query]),
        n_results=result_count,
        include=["documents", "metadatas", "distances"],
    )
    output = []
    for index, document in enumerate(result["documents"][0]):
        distance = float(result["distances"][0][index])
        similarity = max(0.0, min(1.0, 1.0 - distance))
        if similarity < threshold:
            continue

        metadata = result["metadatas"][0][index]
        output.append(
            {
                "id": result["ids"][0][index],
                "document_name": metadata.get("document_name", "Unknown"),
                "document_id": metadata.get("document_id", ""),
                "chunk_index": int(metadata.get("chunk_index", 0)),
                "page_number": (
                    int(metadata["page_number"])
                    if metadata.get("page_number") not in (None, "")
                    else None
                ),
                "similarity": round(similarity, 4),
                "text": document,
            }
        )
    return output


def delete_document(document_id):
    _collection().delete(where={"document_id": document_id})
