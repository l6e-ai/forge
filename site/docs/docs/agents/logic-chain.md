---
title: Build a logic chain agent
description: Orchestrate multiple LLM calls (analyze → plan → answer → refine) in your agent.
---

## Overview

This guide extends the basic assistant by composing several LLM calls into a simple logic chain. We will:

- Analyze the user question
- Produce a step-by-step plan
- Generate an initial answer
- Optionally refine the answer for clarity

You will see both the code to orchestrate the calls and small templates for each step.

## Agent orchestration

Create or edit `agents/<name>/agent.py` to chain multiple calls using the model manager. Below is a minimal example that assumes your agent has a configured model (e.g., in `config.toml` under `[model]`).

```python
from __future__ import annotations

from l6e_forge.core.agents.base import IAgent
from l6e_forge.types.core import AgentContext, AgentResponse, Message
from l6e_forge.types.model import ModelSpec
from l6e_forge.runtime.base import IRuntime
from l6e_forge.prompt import PromptBuilder


class Agent(IAgent):
    name = "logic-chain"
    description = "Agent that composes multiple LLM calls into a logic chain"
    version = "0.1.0"

    async def configure(self, config):
        self.config = config
        model_cfg = getattr(config, "model", {}) if hasattr(config, "model") else (config.get("model", {}) if isinstance(config, dict) else {})
        self._provider = (getattr(model_cfg, "provider", None) if hasattr(model_cfg, "provider") else model_cfg.get("provider")) if model_cfg else None
        self._model = (getattr(model_cfg, "model", None) if hasattr(model_cfg, "model") else model_cfg.get("model")) if model_cfg else None

    async def initialize(self, runtime: IRuntime):
        self.runtime = runtime
        self._prompt = PromptBuilder()

    async def handle_message(self, message: Message, context: AgentContext) -> AgentResponse:
        # Optional: recall related memory
        try:
            mm = self.runtime.get_memory_manager()
            memories = await mm.search_vectors(namespace=self.name, query=message.content, limit=3)
            recall = "\n".join(f"- {m.content}" for m in memories)
            await mm.store_vector(namespace=self.name, key=str(message.message_id), content=message.content, metadata={"role": message.role})
        except Exception:
            recall = ""

        # Load model once
        manager = self.runtime.get_model_manager()
        spec = ModelSpec(
            model_id=self._model or "auto",
            provider=self._provider or "ollama",
            model_name=self._model or "llama3.2:3b",
            memory_requirement_gb=0.0,
        )
        model_id = await manager.load_model(spec)

        # 1) Analyze
        analyze_prompt = await self._prompt.render_from_file(
            "templates/analyze.j2",
            context,
            extra_vars={"user_input": message.content, "recall": recall},
            k_limit=6,
            agent_name=self.name,
        )
        analyze_out = await manager.chat(model_id, [Message(role="user", content=analyze_prompt)])
        analysis = analyze_out.message.content.strip()

        # 2) Plan
        plan_prompt = await self._prompt.render_from_file(
            "templates/plan.j2",
            context,
            extra_vars={"user_input": message.content, "analysis": analysis},
            k_limit=6,
            agent_name=self.name,
        )
        plan_out = await manager.chat(model_id, [Message(role="user", content=plan_prompt)])
        plan = plan_out.message.content.strip()

        # 3) Answer (initial)
        answer_prompt = await self._prompt.render_from_file(
            "templates/answer.j2",
            context,
            extra_vars={"user_input": message.content, "analysis": analysis, "plan": plan, "recall": recall},
            k_limit=8,
            agent_name=self.name,
        )
        answer_out = await manager.chat(model_id, [Message(role="user", content=answer_prompt)])
        answer = answer_out.message.content.strip()

        # 4) Refine (optional)
        refine_prompt = await self._prompt.render_from_file(
            "templates/refine.j2",
            context,
            extra_vars={"draft": answer},
            k_limit=2,
            agent_name=self.name,
        )
        refine_out = await manager.chat(model_id, [Message(role="user", content=refine_prompt)])
        refined = refine_out.message.content.strip()

        return AgentResponse(content=refined or answer, agent_id=self.name, response_time=0.0)
```

Notes:

- We reuse a single `model_id` for all calls in this request.
- We pass outputs between steps via local variables (`analysis`, `plan`, `answer`).
- Each step renders a separate template file to keep prompts small, focused, and testable.

## Step templates

Create these files under `agents/<name>/templates/`.

`templates/analyze.j2`:

```jinja
You are analyzing a user request.
User says: {{ user_input }}

{% if recall %}
Related memory:
{{ recall }}
{% endif %}

Provide a short analysis of the task and any constraints.
```

`templates/plan.j2`:

```jinja
Based on this analysis:
{{ analysis }}

Produce a numbered plan (3-6 steps) to answer the user request.
Keep steps concise and executable.
```

`templates/answer.j2`:

```jinja
You will follow this plan to answer the user:
{{ plan }}

User says: {{ user_input }}

{% if recall %}
Relevant memory:
{{ recall }}
{% endif %}

Write a clear, helpful answer. Keep it brief unless detail is necessary.
```

`templates/refine.j2`:

```jinja
Rewrite the following draft to be clearer and more concise, without losing meaning:

---
{{ draft }}
---

Return only the refined text.
```

## Running

Chat with your agent:

```bash
poetry run forge chat logic-chain -w ./my-workspace
```

If you created a new agent, ensure its `[model]` is configured in `agents/<name>/config.toml`.

## Variations

- Replace the final refine with a format-enforcement step (e.g., JSON schema or Markdown sections).
- Add a verification step that checks for missing constraints, then loops back to improvement.
- Mix providers: use a small local model for analysis/plan and a larger model for answering.


