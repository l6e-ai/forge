---
title: Local Runtime
description: Default local runtime behavior — automatic conversation storage, history access, and provider selection.
sidebar_position: 0
---

### What the Local Runtime Does

The default `LocalRuntime` wires up core services and automates common tasks:

- Registers agents from their directories and manages IDs
- Routes messages and builds a minimal `AgentContext`
- Automatically stores incoming messages to conversation history
- Attaches recent `conversation_history` to the context
- Provides a `history_provider` for lazy history loading
- Lazily initializes a memory manager and model manager

### Automatic Conversation Storage

On each `route_message`, the runtime:

```python
mm = self.get_memory_manager()
await mm.store_conversation(ctx.conversation_id, message)
ctx.conversation_history = await mm.get_conversation(ctx.conversation_id, limit=50)
from l6e_forge.memory.conversation.provider import ConversationHistoryProvider
ctx.history_provider = ConversationHistoryProvider(mm)
```

Agents can immediately use `context.conversation_history` or call the provider for more.

### Memory Manager Selection

The runtime picks defaults then upgrades if providers are available:

- Vector store: In-memory by default; Qdrant if `QDRANT_URL` or `AF_MEMORY_PROVIDER=qdrant`. Backends may support multiple collections.
- Embeddings: Prefer Ollama (`OLLAMA_HOST`), then LM Studio (`LMSTUDIO_HOST`), else a mock embedder.
- Conversation store: Postgres if `AF_DB_URL` is set; otherwise in-memory.

### Model Manager Selection

The model manager is created from endpoints loaded via workspace config (`forge.toml`). Override the default with `AF_DEFAULT_PROVIDER`.

### Environment Variables

- `QDRANT_URL`, `AF_MEMORY_PROVIDER`
- `OLLAMA_HOST`, `LMSTUDIO_HOST`
- `AF_DB_URL`
- `AF_DEFAULT_PROVIDER`

### Practical Usage in an Agent

Because the runtime stores conversation messages automatically and attaches recent history, agents can focus on logic:

```python
async def handle_message(self, message, context):
    # History is already available
    recent = context.conversation_history
    mm = self.runtime.get_memory_manager()
    # Store/query vector memory as needed
    await mm.store_vector(namespace=self.name, key=str(message.message_id), content=message.content)
    hits = await mm.search_vectors(namespace=self.name, query=message.content, limit=5)
    # Build a reply using recall + history
    recall = "\n".join(f"- {m.content}" for m in hits)
    return AgentResponse(content=f"You said: {message.content}\n\n{recall}", agent_id=self.name, response_time=0.0)
```

This behavior is designed for a great local-first developer experience while remaining pluggable via adapters and environment variables.

