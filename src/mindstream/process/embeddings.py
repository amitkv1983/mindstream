from __future__ import annotations

import os

import httpx


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBEDDING_MODEL = "nomic-embed-text"


def generate_embedding(text: str) -> list[float]:
    print(f"[Embeddings] Base URL: {OLLAMA_BASE_URL}")
    print(f"[Embeddings] Model: {EMBEDDING_MODEL}")
    print(f"[Embeddings] Input length: {len(text)}")
    with httpx.Client(timeout=120.0) as client:
        response = client.post(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            json={
                "model": EMBEDDING_MODEL,
                "prompt": text,
            },
        )
        response.raise_for_status()
        data = response.json()
    embedding = data.get("embedding", [])
    vector = [float(value) for value in embedding]
    print(f"[Embeddings] Embedding dimension: {len(vector)}")
    return vector
