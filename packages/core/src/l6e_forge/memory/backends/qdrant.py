from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

import httpx

from l6e_forge.memory.backends.base import IMemoryBackend
from l6e_forge.types.error import HealthStatus


class QdrantVectorStore(IMemoryBackend):
    """Qdrant HTTP backend for vector upsert/search (MVP).

    Creates the collection lazily on first upsert with the observed vector size.
    """

    def __init__(
        self,
        endpoint: str | None = None,
        distance: str = "Cosine",
        api_key: str | None = None,
        timeout: float = 5.0,
    ) -> None:
        self.endpoint = (
            endpoint or os.environ.get("QDRANT_URL") or "http://localhost:6333"
        ).rstrip("/")
        self.distance = distance  # "Cosine" | "Dot" | "Euclid"
        self.api_key = api_key or os.environ.get("QDRANT_API_KEY")
        self.timeout = timeout

    def _headers(self) -> Dict[str, str]:
        h: Dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            h["api-key"] = self.api_key
        return h

    async def connect(self) -> None:
        return None

    async def disconnect(self) -> None:
        return None

    async def health_check(self, collection: str = "default") -> HealthStatus:
        try:
            url = f"{self.endpoint}/collections/{collection}"
            r = httpx.get(url, headers=self._headers(), timeout=self.timeout)
            return HealthStatus(healthy=r.status_code == 200, status="healthy")
        except Exception:
            return HealthStatus(healthy=False, status="unhealthy")

    def _ensure_collection(self, vector_size: int, collection: str = "default") -> None:
        try:
            url = f"{self.endpoint}/collections/{collection}"
            r = httpx.get(url, headers=self._headers(), timeout=self.timeout)
            if r.status_code == 200:
                return
            # Create collection
            payload = {
                "vectors": {"size": vector_size, "distance": self.distance},
            }
            httpx.put(
                url, json=payload, headers=self._headers(), timeout=self.timeout
            ).raise_for_status()
        except Exception as e:
            # Best-effort in MVP
            from l6e_forge.logging import get_logger

            logger = get_logger()
            logger.exception(f"Error ensuring collection {collection}", exc=e)

    def _split_collection_namespace(
        self, namespace: str, collection: str = "default"
    ) -> tuple[str, str]:
        # Support override format: "collection::namespace"
        try:
            if "::" in namespace:
                col, ns = namespace.split("::", 1)
                return col or collection, ns
        except Exception:
            pass
        return collection, namespace

    async def upsert(
        self,
        namespace: str,
        key: str,
        embedding: List[float],
        content: str,
        collection: str = "default",
        metadata: Dict[str, Any] | None = None,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        # Allow collection override via "collection::namespace"
        if collection and "::" not in namespace:
            namespace = f"{collection}::{namespace}"
        collection, ns = self._split_collection_namespace(namespace, collection)
        # Qdrant doesn't have namespaces; emulate by including ns in payload
        self._ensure_collection(len(embedding), collection)
        payload = {
            "points": [
                {
                    "id": key,
                    "vector": embedding,
                    "payload": {
                        "content": content,
                        "metadata": metadata or {},
                        "namespace": ns,
                    },
                }
            ]
        }
        try:
            url = f"{self.endpoint}/collections/{collection}/points?wait=true"
            httpx.put(
                url, json=payload, headers=self._headers(), timeout=self.timeout
            ).raise_for_status()
        except Exception:
            pass

    async def query(
        self,
        namespace: str,
        query_embedding: List[float],
        collection: str = "default",
        limit: int = 10,
    ) -> List[Tuple[str, float, Any]]:
        if collection and "::" not in namespace:
            namespace = f"{collection}::{namespace}"
        collection, ns = self._split_collection_namespace(namespace, collection)
        self._ensure_collection(len(query_embedding), collection)
        payload = {
            "vector": query_embedding,
            "limit": max(1, limit),
            "with_payload": True,
            "filter": {"must": [{"key": "namespace", "match": {"value": ns}}]},
        }
        try:
            url = f"{self.endpoint}/collections/{collection}/points/search"
            r = httpx.post(
                url, json=payload, headers=self._headers(), timeout=self.timeout
            )
            r.raise_for_status()
            items = r.json().get("result") or []
            out: List[Tuple[str, float, Any]] = []
            for it in items:
                pid = str(it.get("id"))
                score = float(it.get("score") or 0.0)
                payload = it.get("payload") or {}
                content = payload.get("content", "")
                meta = payload.get("metadata", {})
                out.append(
                    (
                        pid,
                        score,
                        type("_QItem", (), {"content": content, "metadata": meta})(),
                    )
                )
            return out
        except Exception:
            return []
