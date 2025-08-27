from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

import httpx

from l6e_forge.memory.backends.base import IMemoryBackend
from l6e_forge.types.error import HealthStatus

# TODO support multiple collections

class QdrantVectorStore(IMemoryBackend):
    """Qdrant HTTP backend for vector upsert/search (MVP).

    Creates the collection lazily on first upsert with the observed vector size.
    """

    def __init__(
        self,
        collection: str = "agent_memory",
        endpoint: str | None = None,
        distance: str = "Cosine",
        api_key: str | None = None,
        timeout: float = 5.0,
    ) -> None:
        self.collection = collection
        self.endpoint = (endpoint or os.environ.get("QDRANT_URL") or "http://localhost:6333").rstrip("/")
        self.distance = distance  # "Cosine" | "Dot" | "Euclid"
        self.api_key = api_key or os.environ.get("QDRANT_API_KEY")
        self.timeout = timeout

    def _headers(self) -> Dict[str, str]:
        h: Dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            h["api-key"] = self.api_key
        return h

    async def connect(self) -> None:  # noqa: D401
        return None

    async def disconnect(self) -> None:  # noqa: D401
        return None

    async def health_check(self) -> HealthStatus:
        try:
            url = f"{self.endpoint}/collections/{self.collection}"
            r = httpx.get(url, headers=self._headers(), timeout=self.timeout)
            ok = r.status_code in (200, 404)
            return HealthStatus(healthy=ok, status="healthy" if ok else "unhealthy")  # type: ignore[arg-type]
        except Exception:
            return HealthStatus(healthy=False, status="unhealthy")  # type: ignore[arg-type]

    def _ensure_collection(self, vector_size: int) -> None:
        try:
            url = f"{self.endpoint}/collections/{self.collection}"
            r = httpx.get(url, headers=self._headers(), timeout=self.timeout)
            if r.status_code == 200:
                return
            # Create collection
            payload = {
                "vectors": {"size": vector_size, "distance": self.distance},
            }
            httpx.put(url, json=payload, headers=self._headers(), timeout=self.timeout).raise_for_status()
        except Exception:
            # Best-effort in MVP
            pass

    def _split_collection_namespace(self, namespace: str) -> tuple[str, str]:
        # Support override format: "collection::namespace"
        try:
            if "::" in namespace:
                col, ns = namespace.split("::", 1)
                return col or self.collection, ns
        except Exception:
            pass
        return self.collection, namespace

    async def upsert(
        self,
        namespace: str,
        key: str,
        embedding: List[float],
        content: str,
        metadata: Dict[str, Any] | None = None,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        # Allow collection override via "collection::namespace"
        collection, ns = self._split_collection_namespace(namespace)
        # Qdrant doesn't have namespaces; emulate by including ns in payload
        self._ensure_collection(len(embedding))
        payload = {
            "points": [
                {
                    "id": key,
                    "vector": embedding,
                    "payload": {"content": content, "metadata": metadata or {}, "namespace": ns},
                }
            ]
        }
        try:
            url = f"{self.endpoint}/collections/{collection}/points?wait=true"
            httpx.put(url, json=payload, headers=self._headers(), timeout=self.timeout).raise_for_status()
        except Exception:
            pass

    async def query(self, namespace: str, query_embedding: List[float], limit: int = 10) -> List[Tuple[str, float, Any]]:
        collection, ns = self._split_collection_namespace(namespace)
        self._ensure_collection(len(query_embedding))
        payload = {
            "vector": query_embedding,
            "limit": max(1, limit),
            "with_payload": True,
            "filter": {"must": [{"key": "namespace", "match": {"value": ns}}]},
        }
        try:
            url = f"{self.endpoint}/collections/{collection}/points/search"
            r = httpx.post(url, json=payload, headers=self._headers(), timeout=self.timeout)
            r.raise_for_status()
            items = r.json().get("result") or []
            out: List[Tuple[str, float, Any]] = []
            for it in items:
                pid = str(it.get("id"))
                score = float(it.get("score") or 0.0)
                payload = it.get("payload") or {}
                content = payload.get("content", "")
                meta = payload.get("metadata", {})
                out.append((pid, score, type("_QItem", (), {"content": content, "metadata": meta})()))
            return out
        except Exception:
            return []


