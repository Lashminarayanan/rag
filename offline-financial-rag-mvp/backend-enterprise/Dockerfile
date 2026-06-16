FROM node:20-slim

# Install Python 3 for the RAG query worker subprocess
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-pip python3-venv curl \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3 /usr/bin/python

WORKDIR /app

# ── Python dependencies (slim set for query worker) ──────────
RUN python3 -m pip install --break-system-packages --no-cache-dir \
    "langgraph>=0.2.34" \
    "langchain-core>=0.3.0" \
    "psycopg[binary]>=3.2.1" \
    "python-dotenv>=1.0.1" \
    "requests>=2.32.3" \
    "pypdf>=5.0.0" \
    "pydantic>=2.8.2"

# ── Copy RAG source ─────────────────────────────────────────
COPY rag/app/ /app/rag/app/

# ── Node.js dependencies ────────────────────────────────────
COPY backend-enterprise/package.json backend-enterprise/package-lock.json* /app/backend-enterprise/
WORKDIR /app/backend-enterprise
RUN npm ci --omit=dev 2>/dev/null || npm install --omit=dev

# ── Copy backend source ─────────────────────────────────────
COPY backend-enterprise/src/ /app/backend-enterprise/src/

ENV PYTHON_QUERY_WORKER=python3
ENV RAG_PYTHON_ENTRY=/app/rag/app/query_worker.py

EXPOSE 8080
CMD ["node", "src/server.js"]
