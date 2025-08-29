import pytest

from l6e_forge.memory.backends.qdrant import QdrantVectorStore


@pytest.mark.asyncio
async def test_qdrant_split_collection_namespace() -> None:
    qb = QdrantVectorStore()
    # Use private helper to ensure parsing logic is stable
    col, ns = qb._split_collection_namespace("override::agentX:ns")  # type: ignore[attr-defined]
    assert col == "override"
    assert ns == "agentX:ns"
    col2, ns2 = qb._split_collection_namespace("agentX:ns")  # type: ignore[attr-defined]
    assert col2 == "default"
    assert ns2 == "agentX:ns"
