from __future__ import annotations

from typing import Protocol, List

from l6e_forge.types.core import Message


class IConversationStore(Protocol):
    async def connect(self) -> None:
        ...

    async def store_message(self, conversation_id: str, message: Message) -> None:
        ...

    async def get_messages(self, conversation_id: str, limit: int = 50) -> List[Message]:
        ...


