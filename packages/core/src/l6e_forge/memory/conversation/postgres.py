import asyncpg
import logging
from typing import List
from l6e_forge.types.core import ConversationID

from l6e_forge.types.core import Message
from .base import IConversationStore

logger = logging.getLogger(__name__)


class PostgresConversationStore(IConversationStore):
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(self._dsn, min_size=1, max_size=5)

    async def store_message(
        self, conversation_id: ConversationID, message: Message
    ) -> None:
        if self._pool is None:
            await self.connect()
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                insert into forge.messages (
                    conversation_id,
                    message_id,
                    role,
                    content,
                    timestamp,
                    metadata
                ) values ($1, $2, $3, $4, $5, $6)
                on conflict (message_id) do nothing
                """,
                conversation_id,
                message.message_id,
                message.role,
                message.content,
                message.timestamp,
                message.metadata if hasattr(message, "metadata") else {},
            )

    async def get_messages(
        self, conversation_id: ConversationID, limit: int = 50
    ) -> List[Message]:
        logger.info(
            f"Getting messages for conversation {conversation_id} with limit {limit}"
        )
        if self._pool is None:
            await self.connect()
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                select message_id, role, content, timestamp
                from forge.messages
                where conversation_id = $1
                order by timestamp desc
                limit $2
                """,
                conversation_id,
                limit,
            )
        # Return in chronological order
        items: List[Message] = []
        for r in reversed(rows):
            items.append(
                Message(
                    content=r["content"],
                    role=r["role"],
                    timestamp=r["timestamp"],
                    message_id=r["message_id"],
                    conversation_id=conversation_id,
                )
            )
        return items
