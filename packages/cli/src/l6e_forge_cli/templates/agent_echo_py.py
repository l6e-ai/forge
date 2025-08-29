from __future__ import annotations

AGENT_ECHO_PY = """
from __future__ import annotations

from l6e_forge.types.config import AgentConfig
from l6e_forge.types.core import AgentContext, AgentResponse, Message
from l6e_forge.types.error import HealthStatus
from l6e_forge.runtime.base import IRuntime
from l6e_forge.core.agents.base import IAgent


class Agent(IAgent):
    name = "{{ name }}"
    description = "Basic echo agent"
    version = "0.1.0"

    async def configure(self, config: AgentConfig) -> None:
        pass

    async def initialize(self, runtime: IRuntime) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    async def handle_message(self, message: Message, context: AgentContext) -> AgentResponse:
        return AgentResponse(content=f"Echo: {message.content}", agent_id=self.name, response_time=0.0)

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
