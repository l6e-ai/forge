from typing import Any, Dict, List, Optional, Protocol, Tuple

from l6e_forge.types.error import HealthStatus


class IMemoryBackend(Protocol):
    """Backend storage interface for memory systems.

    Namespace conventions:
    - Backends SHOULD accept logical namespaces as simple strings.
    - Backends MAY also support an override form "collection::namespace" to
      direct operations to a specific backend collection (e.g., Qdrant). This
      keeps the higher-level memory manager API stable while enabling multiple
      collections.
    """

    async def connect(self) -> None:
        """Connect to the storage backend"""
        ...

    async def disconnect(self) -> None:
        """Disconnect from the storage backend"""
        ...

    async def health_check(self, collection: str) -> HealthStatus:
        """Check backend health for a specific collection"""
        ...

    # Vector operations (required)
    async def upsert(
        self,
        namespace: str,
        key: str,
        embedding: List[float],
        content: str,
        collection: str,
        *,
        metadata: Dict[str, Any] | None = None,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        """Insert or update a vector with associated content and metadata.

        Namespace MAY use the override form "collection::namespace" where supported.
        """
        ...

    async def query(
        self,
        namespace: str,
        query_embedding: List[float],
        collection: str,
        *,
        limit: int = 10,
    ) -> List[Tuple[str, float, Any]]:
        """Return list of (key, score, item) tuples sorted by score desc.

        The third element (item) is backend-specific and may expose content/metadata.
        Namespace MAY use the override form "collection::namespace" where supported.
        """
        ...
