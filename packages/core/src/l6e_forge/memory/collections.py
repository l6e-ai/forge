from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class CollectionSpec:
    provider: str = "default"  # e.g., "qdrant", "inmemory"
    collection_name: Optional[str] = (
        None  # backend collection (e.g., qdrant collection)
    )
    namespace_prefix: Optional[str] = (
        None  # logical namespace prefix within the collection
    )


class MemoryCollectionRegistry:
    """Registry mapping agent -> logical collection alias -> CollectionSpec.

    The registry builds a fully-qualified namespace string for use with the
    existing IMemoryManager API, without changing method signatures.

    Convention used for backends that support a single configured collection
    (e.g., current QdrantVectorStore):
      - If a collection_name is resolved, the namespace is encoded as:
            "{collection_name}::${namespace}"
        Backends can parse this to override the target collection.
      - Otherwise, the namespace is returned as-is.
    """

    def __init__(self) -> None:
        self._store: Dict[str, Dict[str, CollectionSpec]] = {}

    def register(
        self,
        agent_name: str,
        alias: str,
        provider: str = "default",
        collection_name: Optional[str] = None,
        namespace_prefix: Optional[str] = None,
    ) -> None:
        agent = self._store.setdefault(agent_name, {})
        agent[alias] = CollectionSpec(
            provider=provider,
            collection_name=collection_name,
            namespace_prefix=namespace_prefix,
        )

    def resolve(self, agent_name: str, alias: str) -> CollectionSpec:
        return self._store.get(agent_name, {}).get(alias, CollectionSpec())

    def build_namespace(
        self,
        agent_name: str,
        alias: str,
        *,
        subspace: Optional[str] = None,
    ) -> str:
        spec = self.resolve(agent_name, alias)
        # Build logical namespace
        parts: list[str] = []
        if spec.namespace_prefix:
            parts.append(spec.namespace_prefix)
        else:
            parts.append(agent_name)
            parts.append(alias)
        if subspace:
            parts.append(subspace)
        logical_ns = ":".join(parts)
        # If a concrete collection is set, encode override using the `collection::namespace` form
        if spec.collection_name:
            return f"{spec.collection_name}::{logical_ns}"
        return logical_ns


_default_registry = MemoryCollectionRegistry()


def get_default_registry() -> MemoryCollectionRegistry:
    return _default_registry
