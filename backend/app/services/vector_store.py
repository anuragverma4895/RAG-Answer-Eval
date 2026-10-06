import chromadb
from app.config import VECTOR_DB_PATH
from app.services.embeddings import encode

client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
collection = client.get_or_create_collection(
    name="rag_answer_eval",
    metadata={"hnsw:space":"cosine"}
)

def add_chunks(chunks):
    if not chunks: return
    texts=[c["text"] for c in chunks]
    collection.add(
        ids=[c["id"] for c in chunks],
        documents=texts,
        metadatas=[{k:str(v) for k,v in c.items() if k not in ("id","text")} for c in chunks],
        embeddings=encode(texts)
    )

def search(query, top_k, threshold):
    if collection.count()==0: return []
    result=collection.query(query_embeddings=encode([query]), n_results=top_k, include=["documents","metadatas","distances"])
    output=[]
    for i,doc in enumerate(result["documents"][0]):
        distance=float(result["distances"][0][i])
        similarity=max(0.0, min(1.0, 1.0-distance))
        if similarity < threshold: continue
        meta=result["metadatas"][0][i]
        output.append({
            "id":result["ids"][0][i],
            "document_name":meta.get("document_name","Unknown"),
            "document_id":meta.get("document_id",""),
            "chunk_index":int(meta.get("chunk_index",0)),
            "page_number":int(meta["page_number"]) if meta.get("page_number") not in (None,"") else None,
            "similarity":round(similarity,4),
            "text":doc
        })
    return output

def delete_document(document_id):
    collection.delete(where={"document_id":document_id})
