from __future__ import annotations

AGENT_ASSISTANT_BASIC_PY = """
from __future__ import annotations

from l6e_forge.types.config import AgentConfig
from l6e_forge.types.core import AgentContext, AgentResponse, Message
from l6e_forge.types.error import HealthStatus
from l6e_forge.runtime.base import IRuntime
from l6e_forge.core.agents.base import IAgent
from l6e_forge.prompt import PromptBuilder


class Agent(IAgent):
    name = "{{ name }}"
    description = "Basic assistant agent"
    version = "0.1.0"

    async def configure(self, config: AgentConfig) -> None:
        self.config = config

    async def initialize(self, runtime: IRuntime) -> None:
        self.runtime = runtime
        self._prompt_builder = PromptBuilder()

    async def shutdown(self) -> None:
        pass

    async def handle_message(self, message: Message, context: AgentContext) -> AgentResponse:
        # Recall top memories and include in reply (MVP)
        try:
            mm = self.runtime.get_memory_manager()
            memories = await mm.search_vectors(namespace="{{ name }}", query=message.content, limit=3)
            recall = "\\n".join(f"- {m.content}" for m in memories)
        except Exception:
            recall = ""
        # Upsert the message into memory
        try:
            mm = self.runtime.get_memory_manager()
            await mm.store_vector(namespace="{{ name }}", key=str(message.message_id), content=message.content, metadata={"role": message.role})
        except Exception:
            pass
        # Build a response using conversation history (last 6 messages) via Jinja2
        template = (
{% raw %}
            "{%- set k = 6 -%}\\n"
            "You are a helpful assistant.\\n\\n"
            "Recent conversation (last {{ k }}):\\n"
            "{%- for m in history_k(k) %}\\n"
            "- [{{ m.role }}] {{ m.content }}\\n"
            "{%- endfor %}\\n\\n"
            "{%- if recall %}\\n"
            "Related memory:\\n"
            "{{ recall }}\\n\\n"
            "{%- endif %}\\n"
            "User says: {{ user_input }}\\n"
            "Provide a concise answer.\\n"
{% endraw %}
        )
        rendered = await self._prompt_builder.render(
            template,
            context,
            extra_vars={"user_input": message.content, "recall": recall},
            k_limit=6,
        )
        reply = rendered
        return AgentResponse(content=reply, agent_id=self.name, response_time=0.0)

    async def can_handle(self, message: Message, context: AgentContext) -> bool:
        return True

    def get_capabilities(self):
        return []

    def get_tools(self):
        # Tools are assigned by the runtime's default toolkit; return empty spec for now.
        return {}

    async def health_check(self) -> HealthStatus:
        return HealthStatus(healthy=True, status="healthy")

    def get_metrics(self):
        return {}
"""
