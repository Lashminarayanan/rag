# Offline Financial RAG MVP

A production-oriented **offline-first MVP** for analyzing annual reports with:

- **Docling** for document parsing and table extraction (with PDF fallback)
- **LangGraph** for agentic workflow orchestration
- **Ollama** for local LLM + embeddings
- **PostgreSQL + pgvector** for semantic retrieval
- **Node.js / Express** backend for **SSE streaming**
- **Streamlit** UI for interactive research

## Architecture

```text
Local PDF folder
   │
   ├── Python ingestion (Docling / PDF fallback)
   │       ├── chunking
   │       ├── metadata extraction
   │       ├── table capture
   │       └── embeddings via Ollama
   │
   ├── PostgreSQL + pgvector
   │       └── stores chunks, metadata, vectors
   │
   ├── Python query worker (LangGraph)
   │       ├── planner
   │       ├── retriever
   │       ├── comparator
   │       ├── summarizer
   │       └── verifier
   │
   ├── Express backend
   │       └── exposes /api/query/stream (SSE)
   │
   └── Streamlit UI
           └── query, evidence review, streaming answer, report export
```

## Folder structure

```text
backend/        # Express SSE API
rag/            # Python ingestion + LangGraph query worker
ui/             # Streamlit app
infra/          # SQL bootstrap + docker compose
sample_data/    # place local annual reports here
```

## Quick start

### 1) Infrastructure

```bash
cd offline-financial-rag-mvp
cp .env.example .env
cd infra
docker compose up -d
```

This starts:
- PostgreSQL with pgvector
- Optional Ollama container (you may also run it natively)

### 2) Python env for RAG + UI

```bash
cd ../rag
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
```

For Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3) Install backend

```bash
cd ../backend
npm install
```

### 4) Pull local Ollama models

```bash
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

### 5) Initialize DB

```bash
cd ../rag
python -m app.init_db
```

### 6) Add documents

Place annual reports in:

```text
sample_data/reports/
```

### 7) Ingest documents

```bash
python -m app.ingest --source ../sample_data/reports
```

### 8) Start backend

```bash
cd ../backend
npm run dev
```

### 9) Start Streamlit UI

```bash
cd ../ui
streamlit run streamlit_app.py
```

## MVP capabilities

- Ingest local PDFs into chunks with provenance metadata
- Vectorize chunks using a local embedding model via Ollama
- Retrieve relevant evidence from pgvector
- Run a simple LangGraph workflow (planner → retriever → comparator → summarizer → verifier)
- Stream response tokens from Python worker → Node SSE → Streamlit UI
- Render citations and evidence cards in the UI

## Important notes

- This codebase is designed as an **MVP starter pack**.
- The Docling adapter includes a **safe fallback to PyPDF** when Docling is unavailable.
- The verifier is intentionally lightweight in this MVP and should be hardened later.
- Table extraction is stored as raw extracted text/markdown in this version.

## Suggested next improvements

1. Add persistent report export to PDF/Markdown
2. Improve chunking for financial tables / footnotes
3. Add multi-document and multi-company comparison
4. Add auth, audit logging, structured tracing
5. Introduce queue-based ingestion for large corpora
