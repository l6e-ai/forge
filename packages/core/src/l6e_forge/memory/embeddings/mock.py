from __future__ import annotations

from typing import List

from .base import IEmbeddingProvider


class MockEmbeddingProvider(IEmbeddingProvider):
    def __init__(self, dim: int = 256) -> None:
        self.dim = dim

    def embed(self, text: str) -> List[float]:
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        outs: list[list[float]] = []
        for t in texts:
            vec = [0.0] * self.dim
            for tok in t.lower().split():
                h = hash(tok) % self.dim
                vec[h] += 1.0
            # L2 normalize
            norm = sum(x * x for x in vec) ** 0.5 or 1.0
            outs.append([x / norm for x in vec])
        return outs
