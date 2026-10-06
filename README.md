# RAG Answer Eval

A full-stack Retrieval-Augmented Generation (RAG) application that answers questions from your own documents and automatically evaluates answer quality.

## Core flow

Document upload → text extraction → chunking → embeddings → ChromaDB retrieval → Gemini answer generation → automated evaluation → SQLite run history

## Features

- Real document upload and indexing
- PDF, TXT and Markdown extraction
- Configurable chunk size and overlap
- Sentence-Transformers embeddings
- ChromaDB cosine-similarity retrieval
- Configurable top-k and similarity threshold
- Grounded Gemini answer generation
- LLM-based evaluation
- Answer Relevance
- Faithfulness / Groundedness
- Context Precision
- Completeness
- Overall Score
- Evaluation reasoning and issue detection
- Dynamic dashboard KPIs
- Persistent evaluation history
- Document deletion with vector cleanup
- Loading, error and empty states
- Responsive black-and-white UI

## Architecture

```mermaid
flowchart LR
    A[React + Vite] -->|REST API| B[FastAPI]
    B --> C[Document Parser]
    C --> D[Chunker]
    D --> E[Sentence Transformers]
    E --> F[(ChromaDB)]
    B --> G[Retriever]
    G --> F
    G --> H[Gemini]
    H --> I[Generated Answer]
    I --> J[LLM Evaluator]
    J --> K[(SQLite)]
```

## Tech stack

Frontend: React, Vite, Lucide React
Backend: Python, FastAPI
LLM: Google Gemini API
Embeddings: Sentence-Transformers (all-MiniLM-L6-v2)
Vector database: ChromaDB
Metadata/history: SQLite
Documents: pypdf

## Evaluation metrics

| Metric | What it measures |
|---|---|
| Answer Relevance | Whether the answer directly addresses the question |
| Faithfulness | Whether answer claims are supported by retrieved context |
| Context Precision | Whether retrieved passages are relevant |
| Completeness | Whether important context-supported information is covered |
| Overall Score | Balanced answer quality |

All scores are generated at runtime by the evaluator; the dashboard does not use hardcoded evaluation scores.

## Local setup

### Frontend

```bash
cd frontend
npm install
cd ..
```

### Backend

From the repository root:

```bash
python -m venv .venv

# Windows
.venv\\Scripts\\activate

# macOS/Linux
source .venv/bin/activate

pip install -r backend/requirements.txt
```

Create a root .env from .env.example and add your Gemini API key:

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash
```

Start the API:

```bash
uvicorn app.main:app --reload --app-dir backend
```

Run frontend and backend in separate terminals.

Frontend: http://localhost:5173
Backend: http://localhost:8000
Health check: http://localhost:8000/api/health

The first startup downloads the Sentence-Transformers embedding model.

## How the RAG pipeline works

1. User uploads a PDF, TXT or Markdown document.
2. FastAPI extracts text and keeps page metadata for PDFs.
3. Text is cleaned and split into overlapping chunks.
4. Sentence-Transformers converts chunks into normalized embeddings.
5. Chunks and metadata are stored in ChromaDB.
6. A user question is embedded with the same model.
7. ChromaDB returns the most similar chunks using cosine distance.
8. Gemini receives the question plus retrieved context and is instructed not to invent information.
9. A second Gemini call evaluates the generated answer against the question and retrieved context.
10. The result and metrics are persisted in SQLite.

## API endpoints

- POST /api/documents/upload
- GET /api/documents
- DELETE /api/documents/{id}
- POST /api/rag/query
- GET /api/evaluations
- GET /api/evaluations/{id}
- GET /api/stats
- GET /api/health

## Environment variables

See .env.example.

Important variables:

- GEMINI_API_KEY
- GEMINI_MODEL
- EMBEDDING_MODEL
- VECTOR_DB_PATH
- SQLITE_PATH
- CHUNK_SIZE
- CHUNK_OVERLAP
- TOP_K
- SIMILARITY_THRESHOLD
- MAX_UPLOAD_MB
- VITE_API_URL

Never commit .env, backend/data, uploaded files or virtual environments.

## Project structure

```text
RAG-Answer-Eval/
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   └── styles.css
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── backend/
│   ├── app/
│   │   ├── routes/
│   │   └── services/
│   ├── tests/
│   └── requirements.txt
├── .env.example
├── .gitignore
├── package.json
└── README.md
```

The root `package.json` provides convenience commands, while application code is separated into `frontend/` and `backend/`.

## Testing

Run backend tests from the repository root:

```bash
pytest backend/tests
```

The tests cover chunking and API health. The live RAG path additionally requires a Gemini API key and local embedding/vector dependencies.

## Screenshots

Add screenshots here after running the project with a real document.

## Interview-ready explanation

RAG Answer Eval is an end-to-end RAG system with an evaluation layer. Instead of asking an LLM to answer from memory, the system first retrieves semantically similar passages from the user's documents. Those passages become the grounded context for Gemini. After generation, another evaluator checks whether the answer is relevant, faithful to the retrieved context, supported by high-quality retrieval, and complete. The application stores every run so quality can be inspected over time.

## Future improvements

- Hybrid BM25 + vector retrieval
- Cross-encoder reranking
- Streaming model responses
- Authentication and per-user knowledge bases
- Background document processing
- Benchmark datasets and regression testing
- Cloud vector database deployment
