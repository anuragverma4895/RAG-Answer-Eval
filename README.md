# RAG Answer Eval

A full-stack Retrieval-Augmented Generation (RAG) application that answers questions from uploaded documents and evaluates each generated answer with a separate LLM-based evaluation step.

## Features

- Upload PDF, TXT, and Markdown documents.
- Extract text, split it into overlapping chunks, and create sentence embeddings.
- Index document chunks in a persistent ChromaDB collection.
- Retrieve relevant passages using cosine similarity and a configurable threshold.
- Generate document-grounded answers with the Google Gemini API.
- Score each answer for relevance, faithfulness, context precision, completeness, and overall quality.
- View retrieved chunks and their relevance scores alongside an answer.
- Review quality metrics, recent outcomes, and saved evaluation history.
- Delete documents and their indexed chunks.
- View document counts, indexed chunks, average evaluation score, groundedness, and latency.

The evaluation scores are LLM-generated quality signals, not guaranteed ground truth. Review the source passages and answer before relying on a score.

## Technology stack

| Layer | Technologies |
|---|---|
| Frontend | React, Vite, Lucide React |
| Backend API | Python, FastAPI, Uvicorn |
| Answer generation and evaluation | Google Gemini API |
| Embeddings | Sentence Transformers, `all-MiniLM-L6-v2` |
| Vector database | ChromaDB |
| Metadata and evaluation history | SQLite |
| PDF text extraction | pypdf |
| Deployment | Docker, Render Blueprint |

## Project structure

```text
RAG-Answer-Eval/
├── .env.example                 # Root-level backend environment template
├── .github/
│   └── workflows/
│       └── ci.yml             # Frontend build and backend test checks
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── documents.py     # Upload, list, and delete documents
│   │   │   ├── evaluations.py   # Evaluation history and details
│   │   │   ├── rag.py           # Retrieval, answer generation, evaluation
│   │   │   └── stats.py         # Dashboard statistics
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── chunking.py      # Text cleanup and overlapping chunks
│   │   │   ├── embeddings.py    # Sentence Transformer model and encoding
│   │   │   ├── llm.py           # Gemini answer and evaluation calls
│   │   │   ├── storage.py       # SQLite persistence
│   │   │   └── vector_store.py  # ChromaDB indexing and search
│   │   ├── config.py            # Environment and runtime configuration
│   │   ├── main.py              # FastAPI app and route registration
│   │   └── schemas.py           # Request/response validation
│   ├── tests/
│   │   ├── test_chunking.py
│   │   ├── test_documents.py
│   │   └── test_health.py
│   ├── data/                    # Created at runtime; ignored by Git
│   ├── requirements.txt         # Runtime dependencies
│   └── requirements-dev.txt     # Runtime plus pytest/httpx for tests
├── frontend/
│   ├── src/
│   │   ├── main.jsx             # UI and API interactions
│   │   └── styles.css
│   ├── index.html
│   ├── package.json
│   └── vite.config.js           # Proxies /api to the local backend
├── .dockerignore
├── .gitignore
├── Dockerfile                   # Builds frontend and runs backend together
├── render.yaml                  # Render service and persistent disk settings
└── README.md
```

Create the local environment file `.env` in the repository root by copying `.env.example`. Keep the real `.env` private and out of Git. Runtime databases and indexed vectors are written to `backend/data/` by default; these are local application data and must not be committed.

## Requirements

- Python 3.11
- Node.js 20 or newer (Node.js 22 is suitable)
- npm
- A Google Gemini API key for answer generation and evaluation

The first embedding operation downloads the Sentence Transformers model. Allow extra time and network access on the first run.

## Local setup

Run the commands from the repository root unless a command explicitly changes directory.

### 1. Create the Python environment

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
Copy-Item .env.example .env
```

**macOS / Linux**

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r backend/requirements-dev.txt
cp .env.example .env
```

Edit the root `.env` and set `GEMINI_API_KEY` to your own key. Do not commit or share that file. The other settings have working defaults.

### 2. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

No frontend `.env` file is needed. In development, Vite proxies `/api` requests to FastAPI on port 8000. In the production Docker image, FastAPI serves the built frontend and API from the same origin.

## Run locally

Start each process in a separate terminal.

**Terminal 1 — Backend**

Windows PowerShell:

```powershell
Set-Location backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

macOS / Linux:

```bash
cd backend
../.venv/bin/python -m uvicorn app.main:app --reload
```

The API is available at:

- App health: http://localhost:8000/api/health
- API documentation: http://localhost:8000/docs

**Terminal 2 — Frontend**

```bash
cd frontend
npm run dev
```

Open the local URL printed by Vite, normally http://localhost:5173. Keep the backend terminal running while using the frontend.

## Backend environment variables

Configure local backend variables in the repository-root `.env`, alongside the `frontend/` and `backend/` directories. Render variables are configured in the service environment and do not require an uploaded `.env` file.

| Variable | Purpose | Default |
|---|---|---|
| `GEMINI_API_KEY` | Required Gemini API key | — |
| `GEMINI_MODEL` | Gemini model used for generation and evaluation | `gemini-2.5-flash` |
| `EMBEDDING_MODEL` | Sentence Transformers model | `all-MiniLM-L6-v2` |
| `VECTOR_DB_PATH` | ChromaDB persistence directory | `./backend/data/chroma` |
| `SQLITE_PATH` | SQLite database path | `./backend/data/rag_eval.db` |
| `CHUNK_SIZE` | Maximum target chunk length, in characters | `800` |
| `CHUNK_OVERLAP` | Overlap between adjacent chunks, in characters | `150` |
| `TOP_K` | Default number of retrieved chunks | `5` |
| `SIMILARITY_THRESHOLD` | Minimum cosine similarity accepted for retrieval (0–1) | `0.25` |
| `MAX_UPLOAD_MB` | Maximum uploaded file size, in MiB | `15` |

Relative data paths are resolved from the repository root, not from the current terminal directory. On Render, `render.yaml` sets the database, vector store, and model cache under the persistent disk mounted at `/var/data`.

## API reference

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/stats` | Dashboard statistics |
| `GET` | `/api/documents` | List indexed and failed documents |
| `POST` | `/api/documents/upload` | Upload and index a PDF, TXT, or Markdown file (multipart field: `file`) |
| `DELETE` | `/api/documents/{document_id}` | Delete a document and its indexed chunks |
| `POST` | `/api/rag/query` | Retrieve context, generate an answer, and evaluate it |
| `GET` | `/api/evaluations` | List recent saved evaluations |
| `GET` | `/api/evaluations/{evaluation_id}` | Get one saved evaluation |

Example request for `POST /api/rag/query`:

```json
{
  "question": "What does the document say about the refund policy?",
  "top_k": 5,
  "similarity_threshold": 0.25
}
```

The API returns the answer, retrieved context chunks, model name, latency, evaluation scores, verdict, reasoning, and potential issues. If no passage meets the similarity threshold, the API returns a not-found response rather than asking Gemini to answer without source context.

## Run tests

Run the tests from the backend directory so the `app` package resolves correctly.

**Windows PowerShell**

```powershell
Set-Location backend
..\.venv\Scripts\python.exe -m pytest tests
```

**macOS / Linux**

```bash
cd backend
../.venv/bin/python -m pytest tests
```

Tests cover text chunking, API health and validation, and document text extraction error cases. A live end-to-end question requires a valid Gemini API key and access to the configured Gemini model.

## Deploy to Render

Use the repository's Blueprint configuration so the Docker service, health check, environment variables, and persistent disk are applied together.

1. Push the repository's `main` branch to GitHub.
2. In Render, choose **New → Blueprint** (not **New Web Service**).
3. Select `anuragverma4895/RAG-Answer-Eval` and the `main` branch.
4. Review the resources defined in `render.yaml`.
5. Enter `GEMINI_API_KEY` when prompted, then apply the Blueprint.
6. Wait for the image build and the `/api/health` check. Open the service URL once it is live.

The root `Dockerfile` builds the React frontend and serves the compiled files through FastAPI, so the UI and API use the same Render web service and URL. No frontend environment variable or separate static-site service is required.

**Cost and storage:** The current Blueprint requests a Standard web instance and a 2 GB persistent disk. These are paid Render resources; review the price shown by Render before confirming. The disk stores ChromaDB, SQLite history, and the model cache across redeploys. The first deployment may take longer while the embedding model is downloaded.

After deployment, check `https://YOUR-SERVICE.onrender.com/api/health`, upload a small text file in Knowledge Base, ask a question grounded in that file, verify that the answer and evaluation metrics appear, and delete the test file to confirm deletion works.

## Known limitations

- Scanned or image-only PDFs do not contain extractable text. OCR is not included.
- Answer generation and quality scoring depend on Gemini API access, quota, and the selected model.
- Evaluation scores are LLM judgements and can vary; they are not a substitute for a manually labelled benchmark.
- Local data lives in `backend/data/`; copy that directory before removing the local environment if you need to preserve it.
