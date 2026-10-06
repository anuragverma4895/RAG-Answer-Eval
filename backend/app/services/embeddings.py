from functools import lru_cache
from sentence_transformers import SentenceTransformer
from app.config import EMBEDDING_MODEL

@lru_cache(maxsize=1)
def model():
    return SentenceTransformer(EMBEDDING_MODEL)

def encode(texts):
    return model().encode(texts, normalize_embeddings=True).tolist()
