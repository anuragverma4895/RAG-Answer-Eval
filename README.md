# RAG Answer Eval

A full-stack Retrieval-Augmented Generation (RAG) application that answers questions from uploaded documents and evaluates answer quality using a separate LLM evaluation step. Results and source metadata are stored locally.

## What it does

1. Upload PDF, TXT, or Markdown documents.
2. Extract text and split it into overlapping chunks.
3. Generate normalized embeddings with Sentence Transformers.
4. Store chunks in ChromaDB and retrieve relevant passages by cosine similarity.
5. Ask Gemini to answer using retrieved source context only.
6. Ask Gemini to evaluate relevance, faithfulness, context precision, completeness, and overall quality.
7. Save evaluation history and metrics in SQLite.

Scores are model-generated evaluations, not ground-truth guarantees. Review the retrieved context and evaluation reasoning before relying on a score.

## Tech stack

- Frontend: React, Vite, Lucide React
- API: Python, FastAPI, Uvicorn
- Generation and evaluation: Google Gemini API
- Embeddings: Sentence Transformers, `all-MiniLM-L6-v2`
- Vector store: ChromaDB
- Metadata and history: SQLite
- PDF extraction: pypdf

## Final project structure

```text
RAG-Answer-Eval/
├── backend/
│   ├── app/
│   │   ├── routes/
│   │   │   ├── documents.py
│   │   │   ├── evaluations.py
│   │   │   ├── rag.py
│   │   │   └── stats.py
│   │   ├── services/
│   │   │   ├── chunking.py
│   │   │   ├── embeddings.py
│   │   │   ├── llm.py
│   │   │   ├── storage.py
│   │   │   └── vector_store.py
│   │   ├── config.py
│   │   ├── main.py
│   │   └── schemas.py
│   ├── tests/
│   ├── data/                 # generated at runtime; not committed
│   ├── dev.mjs               # uses the root .venv to start Uvicorn
│   ├── package.json          # cd backend && npm run dev
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   └── styles.css
│   ├── .env.example
│   ├── index.html
│   ├── package.json          # cd frontend && npm run dev
│   └── vite.config.js
├── .env                      # local-only; create from .env.example
├── .env.example
├── .gitignore
└── README.md
```

The real root `.env`, Python virtual environment, Node dependencies, and `backend/data/` are local-only and should not be committed. The backend uses one root `.env`; do not create a second `backend/.env`.

## One-time setup (Windows PowerShell)

Run these commands from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
Copy-Item .env.example .env
```

Open the root `.env` and set your own Gemini key:

```env
GEMINI_API_KEY=your_actual_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash
```

Keep your key private. Never commit the real `.env`.

Install frontend dependencies:

```powershell
cd frontend
npm install
cd ..
```

## Run locally

Use two VS Code terminals from the project folder.

**Terminal 1 — Backend**

```powershell
cd backend
npm run dev
```

The backend launcher uses the project's root `.venv` automatically.

- API: http://localhost:8000
- Health check: http://localhost:8000/api/health
- Interactive API docs: http://localhost:8000/docs

**Terminal 2 — Frontend**

```powershell
cd frontend
npm run dev
```

Open the Vite URL shown in the terminal, normally http://localhost:5173.

## Environment variables

Root `.env.example` (backend):

| Variable | Purpose |
|---|---|
| `GEMINI_API_KEY` | Gemini API key; required for generation and evaluation |
| `GEMINI_MODEL` | Gemini model name |
| `EMBEDDING_MODEL` | Sentence Transformers model |
| `VECTOR_DB_PATH` | ChromaDB directory; default is `backend/data/chroma` |
| `SQLITE_PATH` | SQLite history database; default is `backend/data/rag_eval.db` |
| `CHUNK_SIZE` | Maximum chunk length in characters |
| `CHUNK_OVERLAP` | Overlap between adjacent chunks |
| `TOP_K` | Default maximum retrieval count |
| `SIMILARITY_THRESHOLD` | Minimum cosine similarity converted to a 0–1 score |
| `MAX_UPLOAD_MB` | Maximum upload size in MiB |

Paths are resolved relative to the repository root even when the backend is launched from the `backend/` directory.

Frontend `frontend/.env.example`:

- `VITE_API_URL`: API base URL; defaults to `http://localhost:8000/api`.

## API endpoints

- `GET /api/health`
- `GET /api/stats`
- `GET /api/documents`
- `POST /api/documents/upload`
- `DELETE /api/documents/{document_id}`
- `POST /api/rag/query`
- `GET /api/evaluations`
- `GET /api/evaluations/{evaluation_id}`

## Tests

From the repository root, with the virtual environment's dependencies installed:

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests
```

The tests cover health and chunking edge cases. A live end-to-end RAG query also needs a valid Gemini API key and access to the configured Gemini model. The first embedding operation downloads the selected Sentence Transformers model.

## Quality and limitations

- Only supported PDF, TXT, and Markdown files are accepted.
- Scanned/image-only PDFs do not contain selectable text and need OCR before upload.
- Document content is treated as untrusted source data in the generation prompt, but prompt-injection resistance is not guaranteed.
- LLM evaluation is a useful signal, not a substitute for human review or a benchmark dataset.
- Local SQLite and ChromaDB data are stored in `backend/data/`; back up that folder if you need to preserve local indexed documents and history.

## Interview explanation

RAG Answer Eval is a document-grounded question-answering application with a separate evaluation layer. It chunks and embeds a user's documents, retrieves semantically relevant passages, sends those passages to Gemini as context, and evaluates the resulting answer for relevance, faithfulness, context precision, and completeness. Each run is persisted so answers and scores can be reviewed instead of relying on a hardcoded demo.
