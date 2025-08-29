from typing import Any, Protocol

from l6e_forge.types.core import Message, ConversationID
from l6e_forge.types.memory import MemoryResult


class IMemoryManager(Protocol):
    """Memory manager interface protocol"""

    # Vector memory (for embeddings, semantic search)
    async def store_vector(
        self,
        namespace: str,
        key: str,
        content: str,
        metadata: dict[str, Any] | None = None,
        *,
        collection: str | None = None,
    ) -> None:
        """Store content with vector embedding"""
        ...

    async def search_vectors(
        self,
        namespace: str,
        query: str,
        collection: str | None = None,
        limit: int = 10,
    ) -> list[MemoryResult]:
        """Search for similar content using vector similarity"""
        ...

    async def search_vectors_multi(
        self,
        namespaces: list[str] | list[tuple[str, str]],
        query: str,
        per_namespace_limit: int = 5,
        overall_limit: int | None = None,
    ) -> list[MemoryResult]:
        """Search across multiple namespaces and return merged results sorted by score.

        - per_namespace_limit controls how many results to fetch from each namespace.
        - overall_limit (if provided) caps total results after merging/sorting.
        """
        ...

    # Key-value memory (for structured data)
    async def store_kv(self, namespace: str, key: str, value: Any) -> None:
        """Store key-value data"""
        ...

    async def get_kv(self, namespace: str, key: str) -> Any:
        """Retrieve key-value data"""
        ...

    async def delete_kv(self, namespace: str, key: str) -> None:
        """Delete key-value data"""
        ...

    # Conversation memory (for chat history)
    async def store_conversation(
        self, conversation_id: ConversationID, message: Message
    ) -> None:
        """Store a conversation message"""
        ...

    async def get_conversation(
        self, conversation_id: ConversationID, limit: int = 50
    ) -> list[Message]:
        """Get conversation history"""
        ...

    # Session memory (temporary, scoped to conversation)
    async def store_session(self, session_id: str, key: str, value: Any) -> None:
        """Store session-scoped data"""
        ...

    async def get_session(self, session_id: str, key: str) -> Any:
        """Get session-scoped data"""
        ...

    async def clear_session(self, session_id: str) -> None:
        """Clear all session data"""
        ...
