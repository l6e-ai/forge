---
title: Customize your agent
description: Edit your agent, add few‑shot examples, and use the Prompt Builder.
---

## Prerequisites

- An initialized workspace with at least one agent created (for example `my-ollama`).
- You can scaffold an assistant-style agent with:

```bash
poetry run forge create agent my-assistant --template=assistant
```

## Agent basics

Your agent lives at `agents/<name>/agent.py`. The minimal shape looks like:

```python
from l6e_forge.core.agents.base import IAgent
from l6e_forge.types.core import AgentContext, AgentResponse, Message
from l6e_forge.runtime.base import IRuntime
from l6e_forge.prompt import PromptBuilder

class Agent(IAgent):
    name = "my-assistant"

    async def configure(self, config):
        self.config = config

    async def initialize(self, runtime: IRuntime):
        self.runtime = runtime
        # Optionally, initialize a prompt builder
        self._prompt = PromptBuilder()

    async def handle_message(self, message: Message, context: AgentContext) -> AgentResponse:
        # Optionally use memory (vector search) to recall related items
        try:
            mm = self.runtime.get_memory_manager()
            memories = await mm.search_vectors(namespace=self.name, query=message.content, limit=3)
            recall = "\n".join(f"- {m.content}" for m in memories)
            await mm.store_vector(namespace=self.name, key=str(message.message_id), content=message.content, metadata={"role": message.role})
        except Exception:
            recall = ""

        rendered = await self._prompt.render_from_file(
            "templates/chat.j2",
            context,
            extra_vars={"user_input": message.content, "recall": recall},
            k_limit=8,
            agent_name=self.name,
        )
        # If your agent uses a model, send `rendered` to your model here.
        # Then return the models response; this is a simple echo implementation:
        return AgentResponse(content=rendered, agent_id=self.name, response_time=0.0)
```

- **`PromptBuilder`** lets you render Jinja templates with conversation history via `history_k(k)`.
- **Memory**: use `runtime.get_memory_manager()` to search and store messages.

## Few‑shot prompting via templates

When you scaffold an agent, a default template is created at `agents/<name>/templates/chat.j2`. Edit that file to add demonstrations (few‑shot examples):

```jinja
{% set k = 8 %}
You are a concise, helpful assistant.

# Few‑shot examples
User: Convert 212 F to C
Assistant: 100 °C

User: Summarize: "Large Language Models are great."
Assistant: LLMs are powerful for many language tasks.

# Conversation context (last {{ k }} messages)
{% for m in history_k(k) %}
- [{{ m.role }}] {{ m.content }}
{% endfor %}

{% if recall %}
Related memory:
{{ recall }}
{% endif %}

User says: {{ user_input }}
Respond with a short, direct answer.
```

Tips:

- Keep few‑shot examples short and style‑consistent with your desired outputs.
- Put stable instructions and examples at the top; append dynamic context (`history_k`, `recall`) below.

## Using a model (optional)

If your agent sends prompts to a model, scaffold with the `assistant` template (already wired for models), or set `model` in `agents/<name>/config.toml`:

```toml
[model]
provider = "ollama"
model = "llama3.2:3b"
```

Then chat:

```bash
poetry run forge chat my-assistant -w ./my-workspace
```

## Debugging prompts

- Render the template string to inspect the exact prompt payload.
- If a variable is missing, the renderer raises an error (StrictUndefined) so you can catch template mistakes early.

## Next steps

- Read the Prompt Builder guide: `using-prompt-builder`
- Explore memory features: `memory/sdk-overview`
 - Build a multi-step logic chain agent: [Build a logic chain agent](agents/logic-chain)


