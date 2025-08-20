from __future__ import annotations

from agent_forge.types.config import AgentConfig
from agent_forge.types.core import AgentContext, AgentResponse, Message
from agent_forge.types.error import HealthStatus
from agent_forge.runtime.base import IRuntime
from agent_forge.core.agents.base import IAgent
from agent_forge.models.managers.lmstudio import LMStudioModelManager


class Agent(IAgent):
    name = "test-unr"
    description = "Assistant agent using lmstudio"
    version = "0.1.0"

    async def configure(self, config: AgentConfig) -> None:
        self.config = config

    async def initialize(self, runtime: IRuntime) -> None:
        self.runtime = runtime

    async def shutdown(self) -> None:
        pass

    async def handle_message(self, message: Message, context: AgentContext) -> AgentResponse:

        manager = self.runtime.get_model_manager() if hasattr(self, 'runtime') and self.runtime else LMStudioModelManager()
        from agent_forge.types.model import ModelSpec
        spec = ModelSpec(model_id="l3-unrestricted", provider="lmstudio", model_name="l3-unrestricted", memory_requirement_gb=0.0)
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