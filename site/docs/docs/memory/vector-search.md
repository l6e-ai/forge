---
title: Memory & Vector Search
description: Store and search vectorized memory using the core SDK.
sidebar_position: 1
---

### Storing and Searching

```python
from l6e_forge.types.core import Message, AgentContext, AgentResponse

async def handle_message(self, message: Message, context: AgentContext) -> AgentResponse:
    mm = self.runtime.get_memory_manager()

    # Store incoming content
    await mm.store_vector(
        namespace="my-agent",               # logical bucket (use namespacing for subareas)
        key=str(message.message_id),         # unique key
        content=message.content,             # text to embed
        metadata={"role": message.role},    # optional metadata
    )

    # Semantic search
    hits = await mm.search_vectors(
        namespace="my-agent",
        query=message.content,
        limit=5,
    )

    recall = "\n".join(f"- {m.content}" for m in hits)
    reply = f"You said: {message.content}\n\nRelated:\n{recall}" if hits else f"You said: {message.content}"
    return AgentResponse(content=reply, agent_id=self.name, response_time=0.0)
```

### Multi-namespace Search

```python
hits = await mm.search_vectors_multi(
    namespaces=["my-agent:short", "my-agent:long"],
    query="project plan",
    per_namespace_limit=3,
    overall_limit=5,
)
```

Each result is a `MemoryResult` with fields like `content`, `score`, `namespace`, and `key`.

### Buckets with Collections

Some backends (e.g., Qdrant, InMemory) support multiple collections. You can treat collections as storage "buckets" alongside namespaces.

Store the same content in two buckets and search each separately:

```python
ns = f"{self.name}:notes"

# Store into short-term bucket
await mm.store_vector(namespace=ns, key=str(message.message_id), content=message.content, metadata={"bucket": "st"}, collection="short_term")

# Store into long-term bucket
await mm.store_vector(namespace=ns, key=str(message.message_id), content=message.content, metadata={"bucket": "lt"}, collection="long_term")

# Search within the short-term bucket
st_hits = await mm.search_vectors(namespace=ns, query="project plan", limit=3, collection="short_term")

# Search within the long-term bucket
lt_hits = await mm.search_vectors(namespace=ns, query="project plan", limit=3, collection="long_term")
```

Search across two buckets at once using multi-search by encoding the collection into the namespace string:

```python
hits = await mm.search_vectors_multi(
    namespaces=[
        f"short_term::{self.name}:notes",  # collection::namespace
        f"long_term::{self.name}:notes",
    ],
    query="project plan",
    per_namespace_limit=3,
    overall_limit=5,
)
```

