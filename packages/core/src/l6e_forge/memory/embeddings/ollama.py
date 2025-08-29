from __future__ import annotations

import os
from typing import List

import httpx

from .base import IEmbeddingProvider


class OllamaEmbeddingProvider(IEmbeddingProvider):
    def __init__(
        self, model: str = "nomic-embed-text:latest", endpoint: str | None = None
    ) -> None:
        self.model = model
        self.endpoint = (
            endpoint or os.environ.get("OLLAMA_HOST") or "http://localhost:11434"
        ).rstrip("/")

    def embed(self, text: str) -> List[float]:
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        url = f"{self.endpoint}/api/embeddings"
        payload = {"model": self.model, "prompt": texts if len(texts) > 1 else texts[0]}
        try:
            resp = httpx.post(url, json=payload, timeout=30.0)
            resp.raise_for_status()
            data = resp.json()
            # Ollama returns either {embedding: [...]} or {embeddings: [[...],[...]]}
            if "embeddings" in data and isinstance(data["embeddings"], list):
                return [list(map(float, v)) for v in data["embeddings"]]
            if "embedding" in data and isinstance(data["embedding"], list):
                return [list(map(float, data["embedding"]))]
        except Exception:
            pass
        # Fallback: zeros
        return [[0.0] * 384 for _ in texts]
