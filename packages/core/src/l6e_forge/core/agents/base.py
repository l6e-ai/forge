from __future__ import annotations

from typing import Any, Protocol, TYPE_CHECKING

from l6e_forge.types.agent import Capability
from l6e_forge.types.config import AgentConfig
from l6e_forge.types.core import AgentContext, AgentResponse, Message
from l6e_forge.types.error import HealthStatus
from l6e_forge.types.tool import ToolSpec

if TYPE_CHECKING:
    from l6e_forge.runtime.base import IRuntime


class IAgent(Protocol):
    """Agent interface protocol"""

    # Agent identity
    name: str
    description: str
    version: str

    # Lifecycle methods
    async def configure(self, config: AgentConfig) -> None:
        """Configure the agent with provided configuration"""
        ...

    async def initialize(self, runtime: IRuntime) -> None:
        """Initialize the agent with runtime dependencies"""
        ...

    async def shutdown(self) -> None:
        """Gracefully shutdown the agent"""
        ...

    # Message handling
    async def handle_message(
        self, message: Message, context: AgentContext
    ) -> AgentResponse:
        """Handle an incoming message and return a response"""
        ...

    async def can_handle(self, message: Message, context: AgentContext) -> bool:
        """Check if this agent can handle the given message"""
        ...

    # Capabilities
    def get_capabilities(self) -> list[Capability]:
        """Get list of agent capabilities"""
        ...

    def get_tools(self) -> dict[str, ToolSpec]:
        """Get available tools for this agent"""
        ...

    # Health and status
    async def health_check(self) -> HealthStatus:
        """Perform health check and return status"""
        ...

    def get_metrics(self) -> dict[str, Any]:
        """Get current metrics for this agent"""
        ...

    def get_result_processor(self):
        """Return an instance implementing `process(response, context)` or None.

        If provided, this takes precedence over `get_result_processor_name` and env defaults.
        """
        ...
