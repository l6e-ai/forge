from __future__ import annotations

AGENT_ASSISTANT_BASIC_PY = """
from __future__ import annotations

from agent_forge.types.config import AgentConfig
from agent_forge.types.core import AgentContext, AgentResponse, Message
from agent_forge.types.error import HealthStatus
from agent_forge.runtime.base import IRuntime
from agent_forge.core.agents.base import IAgent


class Agent(IAgent):
    name = "{{ name }}"
    description = "Basic assistant agent"
    version = "0.1.0"

    async def configure(self, config: AgentConfig) -> None:
        self.config = config

    async def initialize(self, runtime: IRuntime) -> None:
        self.runtime = runtime

    async def shutdown(self) -> None:
        pass

    async def handle_message(self, message: Message, context: AgentContext) -> AgentResponse:
        # Minimal assistant behavior: acknowledge and reflect
        reply = f"I can help. You said: {message.content}"
        return AgentResponse(content=reply, agent_id=self.name, response_time=0.0)

    async def can_handle(self, message: Message, context: AgentContext) -> bool:
        return True

    def get_capabilities(self):
        return []

    def get_tools(self):
        return {}

    async def health_check(self) -> HealthStatus:
        return HealthStatus(healthy=True, status="healthy")

    def get_metrics(self):
        return {}
"""


