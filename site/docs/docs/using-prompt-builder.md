---
sidebar_position: 6
title: Using Prompt Builder
description: Render prompts via Jinja2 with AgentContext and recent conversation history helpers.
---

<!-- Adapted from repo docs/using-prompt-builder.md -->

### PromptBuilder (Jinja2)

Render prompts with Jinja2 using `AgentContext` and k-limited history.

```python
from l6e_forge.prompt import PromptBuilder

builder = PromptBuilder()
rendered = await builder.render(
    """
You are {{ context.agent_id or 'an assistant' }}.

Recent conversation (last {{ k }} messages):
{% for m in history_k(k) %}
- [{{ m.role }}] {{ m.content }}
{% endfor %}

User says: {{ user_input }}
Provide a helpful, concise answer.
""",
    context,
    extra_vars={"user_input": message.content, "k": 8},
    k_limit=8,
)
```

Load from file:

```python
rendered = await builder.render_from_file(
  "chat.j2", context, extra_vars={"user_input": message.content, "k": 8},
  k_limit=8, agent_name="my-agent",
)
```

Template locations searched:
- `<workspace>/templates/`
- `<workspace>/shared/prompts/`
- `<workspace>/agents/<agent>/templates/`


