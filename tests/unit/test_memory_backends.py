import asyncio

import pytest

from l6e_forge.memory.backends.inmemory import InMemoryVectorStore


@pytest.mark.asyncio
async def test_inmemory_collection_override_roundtrip() -> None:
    store = InMemoryVectorStore()
    await store.connect()
    # upsert using collection::namespace format
    ns = "demo_collection::agentA:short"
    emb = [0.1, 0.2, 0.3]
    await store.upsert(namespace=ns, key="k1", embedding=emb, content="hello", metadata={"x": 1})
    out = await store.query(namespace=ns, query_embedding=emb, limit=5)
    assert len(out) == 1
    key, score, item = out[0]
    assert key == "k1"
    assert item.content == "hello"
    assert item.metadata.get("x") == 1


