"""
Lightweight FastAPI embedding microservice.
Loads a sentence-transformers model once at startup and serves
embedding requests over HTTP.  Runs on CPU — no GPU required.
"""

from __future__ import annotations

import os

from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "nomic-ai/nomic-embed-text-v1.5")

app = FastAPI(title="Embedding Service")

print(f"[INFO] Loading embedding model: {MODEL_NAME}")
model = SentenceTransformer(MODEL_NAME, trust_remote_code=True)
print(f"[INFO] Model loaded successfully — dim={model.get_sentence_embedding_dimension()}")


class EmbedRequest(BaseModel):
    texts: list[str]


class EmbedResponse(BaseModel):
    embeddings: list[list[float]]


@app.post("/embed")
def embed(req: EmbedRequest) -> EmbedResponse:
    vectors = model.encode(req.texts, show_progress_bar=False, batch_size=32)
    return EmbedResponse(embeddings=[v.tolist() for v in vectors])


@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL_NAME}
