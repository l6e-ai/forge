from typing import Protocol
from l6e_forge.types.event import Event


class IEventHandler(Protocol):
    """Event handler interface"""

    async def handle_event(self, event: Event) -> bool:
        """Handle an event, return False to stop propagation"""
        ...
