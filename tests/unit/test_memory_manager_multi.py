import pytest

from l6e_forge.memory.backends.inmemory import InMemoryVectorStore
from l6e_forge.memory.managers.memory import MemoryManager
from l6e_forge.memory.embeddings.mock import MockEmbeddingProvider


@pytest.mark.asyncio
async def test_search_vectors_multi_merges_and_sorts() -> None:
    store = InMemoryVectorStore()
    mm = MemoryManager(store, embedder=MockEmbeddingProvider(dim=16))
    # Two namespaces
    await mm.store_vector("nsA", "a1", "alpha beta", {})
    await mm.store_vector("nsA", "a2", "gamma delta", {})
    await mm.store_vector("nsB", "b1", "alpha zeta", {})
    await mm.store_vector("nsB", "b2", "theta iota", {})
    res = await mm.search_vectors_multi(
        ["nsA", "nsB"], query="alpha", per_namespace_limit=2, overall_limit=3
    )
    # Should include alpha-containing items first, max 3 total
    assert 1 <= len(res) <= 3
    # Namespaces are included in results
    assert all(r.namespace in ("nsA", "nsB") for r in res)
    # Rank is assigned sequentially
    assert [r.rank for r in res] == list(range(1, len(res) + 1))


@pytest.mark.asyncio
async def test_manager_explicit_collection_passthrough() -> None:
    store = InMemoryVectorStore()
    mm = MemoryManager(store, embedder=MockEmbeddingProvider(dim=8))
    # Write and read using explicit collection
    await mm.store_vector(
        namespace="agentX:short",
        key="m1",
        content="vector one",
        metadata={"a": 1},
        collection="colA",
    )
    out = await mm.search_vectors(
        namespace="agentX:short", query="vector", limit=5, collection="colA"
    )
    assert any(r.key == "m1" for r in out)
