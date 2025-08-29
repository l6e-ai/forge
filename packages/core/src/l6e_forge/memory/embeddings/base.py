from __future__ import annotations

from typing import List, Protocol


class IEmbeddingProvider(Protocol):
    """Embedding provider interface."""

    def embed(self, text: str) -> List[float]:
        """Return vector embedding for a single string."""
        ...

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Return embeddings for a list of strings."""
        ...
