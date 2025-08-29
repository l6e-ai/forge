from typing import List

from l6e_forge.types.core import ConversationID, Message
from l6e_forge.memory.managers.base import IMemoryManager


class ConversationHistoryProvider:
    """Thin provider to access and append conversation history via the memory manager.

    This decouples agents from specific memory store implementations and exposes
    a minimal, stable API surface for conversation history.
    """

    def __init__(self, memory_manager: IMemoryManager) -> None:
        self._memory_manager = memory_manager

    async def get_recent(
        self, conversation_id: ConversationID, limit: int = 50
    ) -> List[Message]:
        return await self._memory_manager.get_conversation(conversation_id, limit)

    async def append(self, conversation_id: ConversationID, message: Message) -> None:
        await self._memory_manager.store_conversation(conversation_id, message)
