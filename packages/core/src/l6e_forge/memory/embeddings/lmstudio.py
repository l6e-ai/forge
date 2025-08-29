from __future__ import annotations

import os
from typing import List

import httpx

from .base import IEmbeddingProvider


class LMStudioEmbeddingProvider(IEmbeddingProvider):
    def __init__(
        self, model: str = "text-embedding-3-small", endpoint: str | None = None
    ) -> None:
        # LM Studio OpenAI-compatible endpoint
        self.model = model
        self.endpoint = (
            endpoint or os.environ.get("LMSTUDIO_HOST") or "http://localhost:1234/v1"
        ).rstrip("/")

    def embed(self, text: str) -> List[float]:
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        url = f"{self.endpoint}/embeddings"
        payload = {"model": self.model, "input": texts if len(texts) > 1 else texts[0]}
        try:
            resp = httpx.post(url, json=payload, timeout=30.0)
            resp.raise_for_status()
            data = resp.json()
            items = data.get("data") or []
            return [list(map(float, it.get("embedding") or [])) for it in items]
        except Exception:
            pass
        return [[0.0] * 384 for _ in texts]
