from functools import lru_cache

@lru_cache(maxsize=1)
def model():
    # Chroma provides an ONNX Runtime CPU implementation of all-MiniLM-L6-v2.
    # It avoids importing PyTorch/CUDA and keeps the web process lightweight.
    # Loading is lazy so health checks can pass before the model is downloaded.
    from chromadb.utils.embedding_functions.onnx_mini_lm_l6_v2 import ONNXMiniLM_L6_V2

    return ONNXMiniLM_L6_V2()


def encode(texts):
    return model()(texts)
