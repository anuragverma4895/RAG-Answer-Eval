import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT = BACKEND_DIR.parent

# In the Docker image, backend/app is copied to /app/app and requirements.txt
# is copied to /app/requirements.txt. Use /app as the root in that layout.
if not (ROOT / "backend").is_dir() and (BACKEND_DIR / "requirements.txt").is_file():
    ROOT = BACKEND_DIR

load_dotenv(ROOT / ".env")


def _configured_path(name: str, default: Path) -> str:
    """Resolve relative data paths from the repository root, never from the shell cwd."""
    raw = os.getenv(name)
    path = Path(raw).expanduser() if raw else default
    if not path.is_absolute():
        path = ROOT / path
    return str(path.resolve())


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
VECTOR_DB_PATH = _configured_path("VECTOR_DB_PATH", ROOT / "backend" / "data" / "chroma")
SQLITE_PATH = _configured_path("SQLITE_PATH", ROOT / "backend" / "data" / "rag_eval.db")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))
TOP_K = int(os.getenv("TOP_K", "5"))
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.25"))
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "15"))
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".markdown"}

if CHUNK_SIZE < 1:
    raise ValueError("CHUNK_SIZE must be greater than zero.")
if CHUNK_OVERLAP < 0 or CHUNK_OVERLAP >= CHUNK_SIZE:
    raise ValueError("CHUNK_OVERLAP must be >= 0 and smaller than CHUNK_SIZE.")
if not 1 <= TOP_K <= 10:
    raise ValueError("TOP_K must be between 1 and 10.")
if not 0 <= SIMILARITY_THRESHOLD <= 1:
    raise ValueError("SIMILARITY_THRESHOLD must be between 0 and 1.")
if MAX_UPLOAD_MB < 1:
    raise ValueError("MAX_UPLOAD_MB must be at least 1.")

Path(VECTOR_DB_PATH).mkdir(parents=True, exist_ok=True)
Path(SQLITE_PATH).parent.mkdir(parents=True, exist_ok=True)
