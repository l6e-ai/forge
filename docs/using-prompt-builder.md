### PromptBuilder (Jinja2) for Agent prompts

Use `l6e_forge.prompt.PromptBuilder` to render prompts with Jinja2, integrating the agent `AgentContext` and k-limited conversation history.

Example:

```python
from l6e_forge.prompt import PromptBuilder

builder = PromptBuilder()

template = """
You are {{ context.agent_id or 'an assistant' }}.

Recent conversation (last {{ k }} messages):
{% for m in history_k(k) %}
- [{{ m.role }}] {{ m.content }}
{% endfor %}

User says: {{ user_input }}
Provide a helpful, concise answer.
"""

rendered = await builder.render(
    template,
    context,           # AgentContext passed into your agent
    extra_vars={"user_input": message.content, "k": 8},
    k_limit=8,         # fetch up to 8 most recent messages via provider
)

# Use the rendered prompt for your LLM call
```

### Loading external templates

Place templates in any of these locations (first found wins):
- `<workspace>/templates/`
- `<workspace>/shared/prompts/`
- `<workspace>/agents/<agent>/templates/`
- Absolute path passed directly

Example loading from file:

```python
from l6e_forge.prompt import PromptBuilder

builder = PromptBuilder()
rendered = await builder.render_from_file(
    "chat.j2",         # or a subpath, e.g. "my/chat.j2"
    context,
    extra_vars={"user_input": message.content, "k": 8},
    k_limit=8,
    agent_name="my-agent",  # improves lookup into agents/<agent>/templates
)
```

### Packaging templates with .l6e builds

You can include a directory of prompt templates in your `.l6e` by using:

```bash
forge package build ./agents/my-agent --prompts-dir ./agents/my-agent/templates
```

On install, templates are extracted to:
```
<workspace>/prompts/<agent>/...
```
These locations are searched by default by `PromptTemplateLoader`.

Variables available in templates:
- `context`: the `AgentContext` object
- `history`: list[Message] already attached to context
- `history_dicts`: list[dict] with flattened message fields
- `history_k(k)`: helper to get the last k messages from `history`

Notes:
- When `k_limit` is provided to `render`, the builder tries to fetch last `k_limit` messages via `context.history_provider` for freshness. It falls back to `context.conversation_history` if unavailable.
- Jinja2 uses `StrictUndefined` to catch typos in templates early.


