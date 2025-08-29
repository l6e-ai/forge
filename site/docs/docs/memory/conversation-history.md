---
title: Conversation History
description: Store and retrieve chat history via the core SDK.
sidebar_position: 2
---

The memory manager supports storing and retrieving conversation messages using a `ConversationID`.

### Local Runtime: auto-managed history

If you are using the `LocalRuntime` (default), you generally do not need to store messages yourself. The runtime automatically:

- stores each incoming message in the conversation store
- attaches recent `conversation_history` to the `AgentContext`
- provides a `history_provider` on `AgentContext` (used by `PromptBuilder` when you set `k_limit`)

Only store messages manually if you are building a custom runtime or invoking agents directly without going through the runtime.

View the [source code](https://github.com/l6e-ai/forge/blob/main/packages/core/src/l6e_forge/runtime/local.py).

### Store Messages

```python
from l6e_forge.types.core import Message, AgentContext

async def handle_message(self, message: Message, context: AgentContext):
    mm = self.runtime.get_memory_manager()
    # Persist the latest user message
    await mm.store_conversation(context.conversation_id, message)
```

Note: When using `LocalRuntime.route_message(...)`, this store step is already performed for you.

### Read Recent History

```python
history = await mm.get_conversation(context.conversation_id, limit=50)
```

When a conversation store is configured (e.g., Postgres), messages are persisted there; otherwise an in-memory store is used for the session.

You can combine conversation history with vector search to retrieve relevant context for prompting.

