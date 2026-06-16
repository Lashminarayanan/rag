
from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "financial_rag")
POSTGRES_USER = os.getenv("POSTGRES_USER", "rag_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "rag_pass")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "llama3.1:8b")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

# LLM backend: "ollama" (local dev) or "vllm" (GPU / RunPod deployment)
LLM_BACKEND = os.getenv("LLM_BACKEND", "ollama")

# vLLM settings (used when LLM_BACKEND=vllm)
VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:8000")
VLLM_MODEL = os.getenv("VLLM_MODEL", "Qwen/Qwen2.5-7B-Instruct")

# Embedding microservice URL (used when LLM_BACKEND=vllm)
EMBEDDING_API_URL = os.getenv("EMBEDDING_API_URL", "http://localhost:8001")

REPORTS_DIR = os.getenv("REPORTS_DIR", str(ROOT / "sample_data" / "reports"))
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "768"))

# Parsing controls
# USE_DOCLING=false  -> safest setting for MVP
# DOCLING_PREFER=true -> try Docling first if enabled
USE_DOCLING = os.getenv("USE_DOCLING", "false").strip().lower() == "true"
DOCLING_PREFER = os.getenv("DOCLING_PREFER", "false").strip().lower() == "true"
