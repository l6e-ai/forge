from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from l6e_forge.types.error import HealthStatus


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


@dataclass
class _VecItem:
    embedding: List[float]
    content: str
    metadata: Dict[str, Any]
    created_at: float
    ttl_s: Optional[int]


class InMemoryVectorStore:
    """Simple in-memory vector store with per-namespace collections.

    Not for production use. Provides basic upsert and similarity search.
    """

    def __init__(self, default_ttl_seconds: Optional[int] = None) -> None:
        self._namespaces: Dict[str, Dict[str, _VecItem]] = {}
        self._default_ttl = default_ttl_seconds

    async def connect(self) -> None:
        return None

    async def disconnect(self) -> None:
        self._namespaces.clear()

    async def health_check(self) -> HealthStatus:
        return HealthStatus(healthy=True, status="healthy")  # type: ignore[arg-type]

    async def upsert(self, namespace: str, key: str, embedding: List[float], content: str, metadata: Dict[str, Any] | None = None, ttl_seconds: Optional[int] = None) -> None:
        ns = self._namespaces.setdefault(namespace, {})
        ns[key] = _VecItem(embedding=embedding, content=content, metadata=metadata or {}, created_at=time.time(), ttl_s=ttl_seconds if ttl_seconds is not None else self._default_ttl)

    async def query(self, namespace: str, query_embedding: List[float], limit: int = 10) -> List[Tuple[str, float, _VecItem]]:
        ns = self._namespaces.get(namespace) or {}
        now = time.time()
        results: List[Tuple[str, float, _VecItem]] = []
        for key, item in list(ns.items()):
            if item.ttl_s is not None and (now - item.created_at) > item.ttl_s:
                del ns[key]
                continue
            score = _cosine_similarity(query_embedding, item.embedding)
            results.append((key, score, item))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[: max(1, limit)]

