#!/bin/bash
# ──────────────────────────────────────────────────────────────
# RunPod GPU Pod — Startup Script
# Deploy the full Financial RAG stack with vLLM on a GPU pod.
# ──────────────────────────────────────────────────────────────
set -euo pipefail

echo "================================================"
echo "  Financial RAG — RunPod GPU Pod Setup (RTX 4090 / Qwen2.5-7B)"
echo "================================================"

# ── Pre-flight checks ───────────────────────────────────────
if ! nvidia-smi &>/dev/null; then
    echo "ERROR: No NVIDIA GPU detected. This script requires a GPU pod."
    exit 1
fi

echo "GPU detected:"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
echo ""

# ── Locate project ──────────────────────────────────────────
WORKSPACE_DIR="${WORKSPACE_DIR:-/workspace/offline-financial-rag-mvp}"
if [ ! -d "$WORKSPACE_DIR" ]; then
    echo "Project not found at $WORKSPACE_DIR"
    echo "Clone the repo first:"
    echo "  git clone <your-repo-url> $WORKSPACE_DIR"
    exit 1
fi
cd "$WORKSPACE_DIR"

# ── Ensure .env exists ──────────────────────────────────────
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "Created .env from .env.example"
    else
        echo "ERROR: No .env or .env.example found."
        exit 1
    fi
    echo ""
    echo ">> Review .env settings, then re-run:  bash runpod-setup.sh"
    exit 1
fi

# ── Install docker compose plugin if missing ────────────────
if ! docker compose version &>/dev/null; then
    echo "Installing Docker Compose plugin..."
    mkdir -p ~/.docker/cli-plugins
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep '"tag_name"' | head -1 | cut -d'"' -f4)
    curl -SL "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-linux-x86_64" \
         -o ~/.docker/cli-plugins/docker-compose
    chmod +x ~/.docker/cli-plugins/docker-compose
fi

# ── Start infrastructure services first ─────────────────────
echo ""
echo "[1/4] Starting PostgreSQL, Embedding service, and vLLM ..."
docker compose -f docker-compose.gpu.yml up -d postgres embeddings vllm

echo ""
echo "[2/4] Waiting for PostgreSQL ..."
until docker compose -f docker-compose.gpu.yml exec -T postgres pg_isready -U rag_user >/dev/null 2>&1; do
    sleep 2
done
echo "  PostgreSQL is ready."

echo ""
echo "[3/4] Waiting for embedding service ..."
until curl -sf http://localhost:8001/health >/dev/null 2>&1; do
    sleep 5
    echo "  Loading embedding model..."
done
echo "  Embedding service is ready."

echo ""
echo "[3/4] Waiting for vLLM (this may take several minutes on first run) ..."
until curl -sf http://localhost:8000/health >/dev/null 2>&1; do
    sleep 10
    echo "  Still loading LLM model..."
done
echo "  vLLM is ready!"

# ── Start application services ──────────────────────────────
echo ""
echo "[4/4] Starting backend and frontend ..."
docker compose -f docker-compose.gpu.yml up -d backend frontend

# ── Summary ─────────────────────────────────────────────────
IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost")
FRONTEND_PORT=$(grep FRONTEND_PORT .env 2>/dev/null | cut -d= -f2 || echo "3000")
FRONTEND_PORT=${FRONTEND_PORT:-3000}

echo ""
echo "================================================"
echo "  All services are running!  (Qwen2.5-7B on RTX 4090)"
echo "================================================"
echo ""
echo "  Frontend:   http://${IP}:${FRONTEND_PORT}"
echo "  Backend:    http://${IP}:8080"
echo "  vLLM API:   http://${IP}:8000"
echo "  Embeddings: http://${IP}:8001"
echo ""
echo "  To ingest PDF reports into the database:"
echo "    docker compose -f docker-compose.gpu.yml --profile ingest run --rm ingest"
echo ""
echo "  To view logs:"
echo "    docker compose -f docker-compose.gpu.yml logs -f"
echo ""
echo "  To stop everything:"
echo "    docker compose -f docker-compose.gpu.yml down"
echo ""
