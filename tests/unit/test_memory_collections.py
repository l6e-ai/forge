from l6e_forge.memory.collections import MemoryCollectionRegistry


def test_build_namespace_defaults() -> None:
    reg = MemoryCollectionRegistry()
    # No registration: falls back to agent:alias and optional subspace
    ns1 = reg.build_namespace("agentA", "short_term")
    assert ns1 == "agentA:short_term"
    ns2 = reg.build_namespace("agentA", "short_term", subspace="u1")
    assert ns2 == "agentA:short_term:u1"


def test_build_namespace_with_collection_and_prefix() -> None:
    reg = MemoryCollectionRegistry()
    reg.register(
        agent_name="agentB",
        alias="long_term",
        provider="qdrant",
        collection_name="agentB_lt",
        namespace_prefix="agentB:lt",
    )
    ns = reg.build_namespace("agentB", "long_term", subspace="topic123")
    # Encodes collection override and logical namespace together
    assert ns == "agentB_lt::agentB:lt:topic123"


