
from typing import Protocol

from agent_forge.types.error import HealthStatus


class IMemoryBackend(Protocol):
    """Backend storage interface for memory systems"""
    
    async def connect(self) -> None:
        """Connect to the storage backend"""
        ...
    
    async def disconnect(self) -> None:
        """Disconnect from the storage backend"""
        ...
    
    async def health_check(self) -> HealthStatus:
        """Check backend health"""
        ...
