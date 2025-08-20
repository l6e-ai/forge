from __future__ import annotations

from agent_forge.types.config import AgentConfig
from agent_forge.types.core import AgentContext, AgentResponse, Message
from agent_forge.types.error import HealthStatus
from agent_forge.runtime.base import IRuntime
from agent_forge.core.agents.base import IAgent
from agent_forge.types.model import ModelSpec


class Agent(IAgent):
    name = "demo"
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

    async def shutdown(self) -> None:
        pass

    async def handle_message(self, message: Message, context: AgentContext) -> AgentResponse:
        # Use runtime model manager with provider/model resolved by bootstrapper
        manager = self.runtime.get_model_manager()  # type: ignore[attr-defined]
        spec = ModelSpec(
            model_id=self._model or "auto",
            provider=self._provider or "ollama",
            model_name=self._model or "llama3.2:3b",
            memory_requirement_gb=0.0,
        )
        model_id = await manager.load_model(spec)
        chat = await manager.chat(model_id, [message])
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