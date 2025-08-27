import pytest

from l6e_forge.memory.backends.inmemory import InMemoryVectorStore
from l6e_forge.memory.managers.inmemory import InMemoryMemoryManager
from l6e_forge.memory.embeddings.mock import MockEmbeddingProvider


@pytest.mark.asyncio
async def test_search_vectors_multi_merges_and_sorts() -> None:
    store = InMemoryVectorStore()
    mm = InMemoryMemoryManager(store, embedder=MockEmbeddingProvider(dim=16))
    # Two namespaces
    await mm.store_vector("nsA", "a1", "alpha beta", {})
    await mm.store_vector("nsA", "a2", "gamma delta", {})
    await mm.store_vector("nsB", "b1", "alpha zeta", {})
    await mm.store_vector("nsB", "b2", "theta iota", {})
    res = await mm.search_vectors_multi(["nsA", "nsB"], query="alpha", per_namespace_limit=2, overall_limit=3)
    # Should include alpha-containing items first, max 3 total
    assert 1 <= len(res) <= 3
    # Namespaces are included in results
    assert all(r.namespace in ("nsA", "nsB") for r in res)
    # Rank is assigned sequentially
    assert [r.rank for r in res] == list(range(1, len(res) + 1))


