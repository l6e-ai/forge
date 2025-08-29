---
title: Agent Forge Context Prompt
description: Build prompts using AgentContext fields and recent history helpers via Prompt Builder.
---

<!-- Imported from repo docs/prompt/agent-forge-context-prompt.md (condensed) -->

Use Prompt Builder helpers like `history_k(k)` to inject recent conversation and `AgentContext` fields into your prompts. Pair with memory search to prepend relevant context before LLM calls.

### What is Prompt Builder?

**Prompt Builder** renders Jinja2 templates with your `AgentContext` and recent conversation history.

- **history helpers**: `history_k(k)` yields the last k `Message`s; `history` is the full list (or limited by `k_limit`).
- **context access**: `context` exposes `AgentContext` values (e.g., `context.user_id`, `context.session_id`).
- **strict templates**: undefined Jinja2 variables raise errors to catch typos early.

Core API:

```python
from l6e_forge.prompt import PromptBuilder

builder = PromptBuilder()
rendered: str = await builder.render(template_str, context, extra_vars={"k": 8}, k_limit=8)
# or from a file that the loader can locate
rendered: str = await builder.render_from_file(
    "answer.j2", context, extra_vars={"k": 8}, k_limit=8, agent_name="my-agent"
)
```

### Quick start (inline template)

```python
template = (
    "You are a helpful assistant.\n\n"
    "Recent conversation (last {{ k }}):\n"
    "{%- for m in history_k(k) %}\n"
    "- [{{ m.role }}] {{ m.content }}\n"
    "{%- endfor %}\n\n"
    "User message: {{ history[-1].content if history else '' }}\n"
)

rendered = await PromptBuilder().render(template, context, extra_vars={"k": 6}, k_limit=6)
```

- **k_limit**: fetches last k messages via the configured history provider on `AgentContext` (falls back to `context.conversation_history`).
- **extra_vars**: any variables you want available in the template (here, `k`).

### File-based templates and search paths

Use `render_from_file(template_ref, ...)` to keep prompts in your workspace. The loader searches, in order:

- **absolute path** to the file
- provided `search_paths` (if you constructed `PromptBuilder(search_paths=[...])`)
- workspace defaults (when `workspace_root` is provided or implied by `context.workspace_path`):
  - `workspace_root/templates/<template_ref>`
  - `workspace_root/shared/prompts/<template_ref>`
  - `workspace_root/agents/<agent_name>/templates/<template_ref>`
  - `workspace_root/prompts/<agent_name>/<template_ref>`
  - `workspace_root/prompts/<template_ref>`
  - current working directory as a last fallback

Example usage:

```python
rendered = await PromptBuilder().render_from_file(
    "assistants/answer.j2",  # relative to search paths described above
    context,
    extra_vars={"k": 8, "topic": "python"},
    k_limit=8,
    agent_name="my-agent",
)
```

Example `assistants/answer.j2`:

```jinja2
You are an assistant specialized in {{ topic }}.

Session: {{ context.session_id }}  User: {{ context.user_id or 'anonymous' }}

Recent conversation (last {{ k }} messages):
{% for m in history_k(k) %}
- [{{ m.role }}] {{ m.content }}
{% endfor %}

Provide a concise answer and, if helpful, a short example.
```

### Building custom prompt chains for agents

You can compose multi-step prompts where each step renders a template (or transforms prior outputs) and optionally calls a model. Below are two common patterns.

- **Two-stage classify → answer** (lightweight routing):

```python
from l6e_forge.prompt import PromptBuilder
from l6e_forge.types.core import Message, AgentResponse

class MyAgent(IAgent):
    async def initialize(self, runtime: IRuntime) -> None:
        self.runtime = runtime
        self._pb = PromptBuilder()

    async def handle_message(self, message: Message, context: AgentContext) -> AgentResponse:
        manager = await self.runtime.get_model_manager("ollama")
        spec = ModelSpec(provider="ollama", model="llama3:8b-instruct")
        model_id = await manager.load_model(spec)

        classify_tmpl = """
        Classify the user's intent as one of: [code, docs, chat].
        Return ONLY the label.
        User: {{ history[-1].content if history else '' }}
        """
        label = (await self._pb.render(classify_tmpl, context, k_limit=1)).strip().lower()

        if label == "code":
            answer_file = "chains/code-answer.j2"
        elif label == "docs":
            answer_file = "chains/docs-answer.j2"
        else:
            answer_file = "chains/chat-answer.j2"

        rendered = await self._pb.render_from_file(answer_file, context, extra_vars={"k": 8}, k_limit=8)
        prompt_msg = Message(role="user", content=rendered)
        chat = await manager.chat(model_id, [prompt_msg])
        return AgentResponse(content=chat.message.content, agent_id=self.name, response_time=0.0)
```

- **Memory-augmented chain** (retrieve → compose → answer):

```python
# 1) Retrieve relevant memory (pseudo-code – adapt to your memory backend)
top_memories = await runtime.memory.search("qdrant", query=message.content, k=5)

# 2) Render an answer prompt with retrieved memory
rendered = await self._pb.render_from_file(
    "chains/rag-answer.j2",
    context,
    extra_vars={"k": 8, "memories": top_memories},
    k_limit=8,
)
```

Example `chains/rag-answer.j2`:

```jinja2
You are a knowledgeable assistant.

Relevant context:
{% for m in memories %}
- {{ m.text }}
{% endfor %}

Conversation (last {{ k }}):
{% for m in history_k(k) %}
- [{{ m.role }}] {{ m.content }}
{% endfor %}

Answer the user's latest question using the context when helpful.
```

### Tips and troubleshooting

- **Undefined variable errors**: Prompt Builder uses strict undefineds. Ensure every variable in your template is passed via `extra_vars` or available as `context`, `history`, `history_k`, or `history_dicts`.
- **history vs k_limit**: `history_k(k)` slices whatever `history` is available. Use `k_limit` to fetch recent messages from the history provider (if configured) before rendering.
- **Template not found**: Double-check the search paths described above. For agent-scoped prompts, prefer `prompts/<agent_name>/...` or `agents/<agent_name>/templates/...`.
- **Template debugging**: Start small; render a minimal template string with `render(...)` and print the output, then move to files.

