from functools import lru_cache

from app.config import EMBEDDING_MODEL


@lru_cache(maxsize=1)
def model():
    # Keep PyTorch out of API startup; load it only when a document or query
    # actually needs an embedding. Production runs CPU-only on Render.
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBEDDING_MODEL, device="cpu")


def encode(texts):
    return model().encode(texts, normalize_embeddings=True).tolist()
