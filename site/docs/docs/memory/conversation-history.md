---
title: Conversation History
description: Store and retrieve chat history via the core SDK.
sidebar_position: 2
---

The memory manager supports storing and retrieving conversation messages using a `ConversationID`.

### Store Messages

```python
from l6e_forge.types.core import Message, AgentContext

async def handle_message(self, message: Message, context: AgentContext):
    mm = self.runtime.get_memory_manager()
    # Persist the latest user message
    await mm.store_conversation(context.conversation_id, message)
```

### Read Recent History

```python
history = await mm.get_conversation(context.conversation_id, limit=50)
```

When a conversation store is configured (e.g., Postgres), messages are persisted there; otherwise an in-memory store is used for the session.

You can combine conversation history with vector search to retrieve relevant context for prompting.

