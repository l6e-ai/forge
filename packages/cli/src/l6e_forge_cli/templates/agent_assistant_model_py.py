from __future__ import annotations

AGENT_ASSISTANT_MODEL_PY = """
from __future__ import annotations

from l6e_forge.types.config import AgentConfig
from l6e_forge.types.core import AgentContext, AgentResponse, Message
from l6e_forge.types.error import HealthStatus
from l6e_forge.runtime.base import IRuntime
from l6e_forge.core.agents.base import IAgent
from l6e_forge.types.model import ModelSpec
from l6e_forge.prompt import PromptBuilder


class Agent(IAgent):
    name = "{{ name }}"
    description = "Assistant agent using auto-bootstrap models"
    version = "0.1.0"

    async def configure(self, config: AgentConfig) -> None:
        self.config = config
        # Bootstrapper populates these fields in config.toml
        model_cfg = getattr(config, "model", {}) if hasattr(config, "model") else (config.get("model", {}) if isinstance(config, dict) else {})
        self._provider = (getattr(model_cfg, "provider", None) if hasattr(model_cfg, "provider") else model_cfg.get("provider")) if model_cfg else None
        self._model = (getattr(model_cfg, "model", None) if hasattr(model_cfg, "model") else model_cfg.get("model")) if model_cfg else None

    async def initialize(self, runtime: IRuntime) -> None:
        self.runtime = runtime
        self._prompt_builder = PromptBuilder()

    async def shutdown(self) -> None:
        pass

    async def handle_message(self, message: Message, context: AgentContext) -> AgentResponse:
        # Recall and store memory (MVP)
        try:
            mm = self.runtime.get_memory_manager()  # type: ignore[attr-defined]
            memories = await mm.search_vectors(namespace="{{ name }}", query=message.content, limit=3)
            recall = "\\n".join(f"- {m.content}" for m in memories)
            await mm.store_vector(namespace="{{ name }}", key=str(message.message_id), content=message.content, metadata={"role": message.role})
        except Exception:
            recall = ""

        # Use runtime model manager with provider/model resolved by bootstrapper
        manager = self.runtime.get_model_manager()  # type: ignore[attr-defined]
        spec = ModelSpec(
            model_id=self._model or "auto",
            provider=self._provider or "ollama",
            model_name=self._model or "llama3.2:3b",
            memory_requirement_gb=0.0,
        )
        model_id = await manager.load_model(spec)
        # Build a prompt using conversation history (last 8 messages) via Jinja2
        template = (
{% raw %}
            "{% set k = 8 %}\\n"
            "You are an assistant.\\n\\n"
            "Recent conversation (last {{ k }} messages):\\n"
            "{% for m in history_k(k) %}\\n"
            "- [{{ m.role }}] {{ m.content }}\\n"
            "{% endfor %}\\n\\n"
            "{% if recall %}\\n"
            "Related memory:\\n"
            "{{ recall }}\\n"
            "{% endif %}\\n\\n"
            "User says: {{ user_input }}\\n"
            "Respond helpfully.\\n"
{% endraw %}
        )
        rendered = await self._prompt_builder.render(
            template,
            context,
            extra_vars={"user_input": message.content, "recall": recall},
            k_limit=8,
        )
        prompt_msg = Message(role="user", content=rendered)
        chat = await manager.chat(model_id, [prompt_msg])
        return AgentResponse(content=chat.message.content, agent_id=self.name, response_time=0.0)

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
