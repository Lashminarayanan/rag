from __future__ import annotations

import json
import requests
from typing import Generator, List
from .config import (
    LLM_BACKEND,
    OLLAMA_BASE_URL, OLLAMA_CHAT_MODEL, OLLAMA_EMBED_MODEL,
    VLLM_BASE_URL, VLLM_MODEL, EMBEDDING_API_URL,
)


# ── Embeddings ───────────────────────────────────────────────

def embed_texts(texts: List[str]) -> List[List[float]]:
    if LLM_BACKEND == "vllm":
        return _embed_via_service(texts)
    return _embed_via_ollama(texts)


def _embed_via_service(texts: List[str]) -> List[List[float]]:
    """Call the embedding microservice (used in Docker / RunPod)."""
    print(f"[INFO] Embedding {len(texts)} chunks via embedding service ...")
    response = requests.post(
        f"{EMBEDDING_API_URL}/embed",
        json={"texts": texts},
        timeout=300,
    )
    response.raise_for_status()
    result = response.json()["embeddings"]
    print(f"[INFO] Completed embeddings for {len(texts)} chunks")
    return result


def _embed_via_ollama(texts: List[str]) -> List[List[float]]:
    """Original Ollama embedding path (local dev)."""
    vectors: List[List[float]] = []
    total = len(texts)
    for idx, text in enumerate(texts, start=1):
        print(f"[INFO] Embedding chunk {idx}/{total} ...")
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            json={"model": OLLAMA_EMBED_MODEL, "prompt": text},
            timeout=120,
        )
        response.raise_for_status()
        vectors.append(response.json()['embedding'])
    print(f"[INFO] Completed embeddings for {total} chunks")
    return vectors


# ── Text generation (streaming) ──────────────────────────────

def generate_answer_stream(prompt: str) -> Generator[str, None, None]:
    if LLM_BACKEND == "vllm":
        yield from _generate_via_vllm(prompt)
    else:
        yield from _generate_via_ollama(prompt)


def _generate_via_vllm(prompt: str) -> Generator[str, None, None]:
    """Stream tokens from vLLM's OpenAI-compatible chat/completions API."""
    response = requests.post(
        f"{VLLM_BASE_URL}/v1/chat/completions",
        json={
            "model": VLLM_MODEL,
            "messages": [
                {"role": "system", "content": "You are a financial research assistant running completely offline. Answer questions accurately based only on the provided evidence. Include citation markers."},
                {"role": "user", "content": prompt},
            ],
            "stream": True,
            "max_tokens": 2048,
            "temperature": 0.1,
            "top_p": 0.9,
        },
        stream=True,
        timeout=600,
    )
    response.raise_for_status()
    for line in response.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data: "):
            continue
        payload = line[len("data: "):]
        if payload.strip() == "[DONE]":
            break
        data = json.loads(payload)
        choices = data.get("choices", [])
        if choices:
            delta = choices[0].get("delta", {})
            if token := delta.get("content"):
                yield token


def _generate_via_ollama(prompt: str) -> Generator[str, None, None]:
    """Original Ollama generation path (local dev)."""
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json={"model": OLLAMA_CHAT_MODEL, "prompt": prompt, "stream": True},
        stream=True,
        timeout=600,
    )
    response.raise_for_status()
    for line in response.iter_lines(decode_unicode=True):
        if not line:
            continue
        data = json.loads(line)
        if token := data.get('response'):
            yield token
        if data.get('done'):
            break
