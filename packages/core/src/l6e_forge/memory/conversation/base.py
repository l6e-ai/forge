from typing import Protocol, List
from l6e_forge.types.core import ConversationID

from l6e_forge.types.core import Message


class IConversationStore(Protocol):
    async def connect(self) -> None: ...

    async def store_message(
        self, conversation_id: ConversationID, message: Message
    ) -> None: ...

    async def get_messages(
        self, conversation_id: ConversationID, limit: int = 50
    ) -> List[Message]: ...
