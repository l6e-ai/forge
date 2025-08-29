---
title: SDK Overview
description: How to use the Forge core SDK in agents, focusing on memory, search, and history.
sidebar_position: 0
---

## Core Concepts

- The core SDK (`l6e-forge`) provides programmatic access to memory, models, and runtime context.
- Use the runtime to obtain managers, e.g., `get_memory_manager()`.

## Getting a Memory Manager

```python
mm = self.runtime.get_memory_manager()
```

You can then use vector memory, key–value memory, and conversation/session helpers.

## Message and Context Types

`l6e_forge.types.core` provides `Message`, `AgentContext`, and `ConversationID`.

```python
from l6e_forge.types.core import Message, AgentContext
```

See the dedicated pages for details:

- Memory & Vector Search
- Conversation History

