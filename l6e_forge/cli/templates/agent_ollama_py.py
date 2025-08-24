from __future__ import annotations

AGENT_OLLAMA_PY = """
from __future__ import annotations

from l6e_forge.types.config import AgentConfig
from l6e_forge.types.core import AgentContext, AgentResponse, Message
from l6e_forge.types.error import HealthStatus
from l6e_forge.runtime.base import IRuntime
from l6e_forge.models.managers.ollama import IModelManager, OllamaModelManager
from l6e_forge.types.model import ModelSpec
from l6e_forge.core.agents.base import IAgent


class Agent(IAgent):
    name = "{{ name }}"
    description = "Ollama-powered agent"
    version = "0.1.0"

    async def configure(self, config: AgentConfig) -> None:
        pass

    async def initialize(self, runtime: IRuntime) -> None:
        self.runtime = runtime

    async def shutdown(self) -> None:
        pass

    async def handle_message(self, message: Message, context: AgentContext) -> AgentResponse:
        # Recall and store memory around the conversation
        try:
            mm = self.runtime.get_memory_manager()  # type: ignore[attr-defined]
            memories = await mm.search_vectors(namespace="{{ name }}", query=message.content, limit=3)
            recall = "\\n".join(f"- {m.content}" for m in memories)
            await mm.store_vector(namespace="{{ name }}", key=message.message_id, content=message.content, metadata={"role": message.role})
        except Exception:
            recall = ""
        # Prefer runtime's model manager when available
        runtime = self.runtime
        manager: IModelManager
        if runtime is not None:
            manager = runtime.get_model_manager()  # type: ignore[attr-defined]
        else:
            endpoint = "{{ endpoint }}"
            manager = OllamaModelManager(endpoint=endpoint) if endpoint else OllamaModelManager()
        spec = ModelSpec(
            model_id="{{ model }}",
            provider="ollama",
            model_name="{{ model }}",
            memory_requirement_gb=0.0,
        )
        model_id = await manager.load_model(spec)
        # Prepend recalled context in a system message
        sys_preface = f"You may use this related memory to answer:\\n{recall}\\n\\n" if recall else ""
        prompt_msg = Message(role="user", content=sys_preface + message.content)
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


