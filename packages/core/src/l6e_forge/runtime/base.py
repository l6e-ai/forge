from __future__ import annotations

from pathlib import Path
from typing import Callable, Protocol, TYPE_CHECKING

from l6e_forge.events.bus.base import IEventBus
from l6e_forge.memory.managers.base import IMemoryManager
from l6e_forge.tools.registry.base import IToolRegistry
from l6e_forge.models.managers.base import IModelManager

from l6e_forge.types.agent import AgentSpec
from l6e_forge.types.core import AgentID, AgentResponse, Message

if TYPE_CHECKING:
    from l6e_forge.core.agents.base import IAgent


class IRuntime(Protocol):
    """Runtime interface protocol"""

    # Agent management
    async def register_agent(self, agent_path: Path) -> AgentID:
        """Register a new agent from the given path"""
        ...

    async def unregister_agent(self, agent_id: AgentID) -> None:
        """Unregister an agent"""
        ...

    async def reload_agent(self, agent_id: AgentID) -> None:
        """Reload an agent (hot reload)"""
        ...

    async def get_agent(self, agent_id: AgentID) -> IAgent:
        """Get agent instance by ID"""
        ...

    async def list_agents(self) -> list[AgentSpec]:
        """List all registered agents"""
        ...

    # Message routing
    async def route_message(
        self, message: Message, target: AgentID | None = None
    ) -> AgentResponse:
        """Route a message to appropriate agent(s)"""
        ...

    async def broadcast_message(
        self, message: Message, filter_fn: Callable | None = None
    ) -> list[AgentResponse]:
        """Broadcast message to multiple agents"""
        ...

    # Resource management
    def get_memory_manager(self) -> IMemoryManager:
        """Get the memory manager instance"""
        ...

    def get_model_manager(self) -> IModelManager:
        """Get the model manager instance"""
        ...

    def get_tool_registry(self) -> IToolRegistry:
        """Get the tool registry instance"""
        ...

    def get_event_bus(self) -> IEventBus:
        """Get the event bus instance"""
        ...

    # Development support
    async def start_dev_mode(self, port: int = 8123) -> None:
        """Start development mode with monitoring UI"""
        ...

    async def enable_hot_reload(self, watch_paths: list[Path]) -> None:
        """Enable hot reloading for specified paths"""
        ...
