import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", str(ROOT / "data" / "chroma"))
SQLITE_PATH = os.getenv("SQLITE_PATH", str(ROOT / "data" / "rag_eval.db"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))
TOP_K = int(os.getenv("TOP_K", "5"))
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.25"))
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "15"))
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".markdown"}

Path(VECTOR_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
Path(SQLITE_PATH).parent.mkdir(parents=True, exist_ok=True)
