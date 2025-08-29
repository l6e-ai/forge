from typing import Protocol

from l6e_forge.types.core import AgentID, SubscriptionID
from l6e_forge.types.event import Event
from l6e_forge.events.handlers.base import IEventHandler


class IEventBus(Protocol):
    """Event bus interface protocol"""

    # Publishing
    async def publish(self, event: Event) -> None:
        """Publish an event to the bus"""
        ...

    async def publish_to_agent(self, agent_id: AgentID, event: Event) -> None:
        """Publish an event to a specific agent"""
        ...

    # Subscribing
    async def subscribe(
        self, event_type: str, handler: IEventHandler
    ) -> SubscriptionID:
        """Subscribe to events of a specific type"""
        ...

    async def subscribe_agent(
        self, agent_id: AgentID, event_type: str, handler: IEventHandler
    ) -> SubscriptionID:
        """Subscribe an agent to events"""
        ...

    async def unsubscribe(self, subscription_id: SubscriptionID) -> None:
        """Unsubscribe from events"""
        ...

    # Event querying
    async def get_event_history(self, event_type: str, limit: int = 100) -> list[Event]:
        """Get event history for a specific type"""
        ...

    async def get_agent_events(
        self, agent_id: AgentID, limit: int = 100
    ) -> list[Event]:
        """Get events related to a specific agent"""
        ...
