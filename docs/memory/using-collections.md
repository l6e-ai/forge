### Using multiple memory collections per agent

This example shows how to use `MemoryCollectionRegistry` to work with multiple logical collections (e.g., short-term and long-term) on top of any backend (InMemory or Qdrant). Backends that support overriding the concrete collection can use the `collection::namespace` form automatically encoded by the registry.

Key ideas:
- Register aliases per agent with optional `collection_name` and `namespace_prefix`.
- Build the namespace via the registry, then call the existing memory manager API.

Minimal agent example:

```python
from __future__ import annotations

from l6e_forge.types.core import AgentContext, AgentResponse, Message
from l6e_forge.types.error import HealthStatus
from l6e_forge.runtime.base import IRuntime
from l6e_forge.core.agents.base import IAgent
from l6e_forge.types.model import ModelSpec
from l6e_forge.memory.collections import get_default_registry


class Agent(IAgent):
    name = "multi-memory"
    description = "Demo agent using multiple memory collections"
    version = "0.1.0"

    async def initialize(self, runtime: IRuntime) -> None:
        self.runtime = runtime
        # Register logical collections for this agent
        reg = get_default_registry()
        # Short-term collection (override backend collection where supported)
        reg.register(
            agent_name=self.name,
            alias="short_term",
            provider="qdrant",
            collection_name=f"{self.name}_st",
            namespace_prefix=f"{self.name}:st",
        )
        # Long-term collection
        reg.register(
            agent_name=self.name,
            alias="long_term",
            provider="qdrant",
            collection_name=f"{self.name}_lt",
            namespace_prefix=f"{self.name}:lt",
        )

    async def handle_message(self, message: Message, context: AgentContext) -> AgentResponse:
        reg = get_default_registry()
        mm = self.runtime.get_memory_manager()  # type: ignore[attr-defined]

        # Build namespaces
        ns_st = reg.build_namespace(self.name, "short_term")
        ns_lt = reg.build_namespace(self.name, "long_term")

        # Store the incoming message in short-term memory
        try:
            await mm.store_vector(namespace=ns_st, key=str(message.message_id), content=message.content, metadata={"role": message.role})
        except Exception:
            pass

        # Query both collections
        try:
            st_hits = await mm.search_vectors(namespace=ns_st, query=message.content, limit=3)
        except Exception:
            st_hits = []
        try:
            lt_hits = await mm.search_vectors(namespace=ns_lt, query=message.content, limit=3)
        except Exception:
            lt_hits = []

        recall_text = "\n".join([f"- [st] {m.content}" for m in st_hits] + [f"- [lt] {m.content}" for m in lt_hits])

        # Echo back with recall
        reply = f"You said: {message.content}\n\nRelated memory:\n{recall_text}" if recall_text else f"You said: {message.content}"
        return AgentResponse(content=reply, agent_id=self.name, response_time=0.0)

    async def can_handle(self, message: Message, context: AgentContext) -> bool:
        return True

    def get_capabilities(self):
        return []

    def get_tools(self):
        return {}

    async def health_check(self) -> HealthStatus:
        return HealthStatus(healthy=True, status="healthy")
```

Notes:
- The registry emits a namespace like `mycollection::agent:alias[:subspace]`. Backends that support collection override (Qdrant, InMemory) will parse this and route to the correct collection.
- For InMemory, the collection part is ignored in storage but the namespace after `::` is used consistently.


