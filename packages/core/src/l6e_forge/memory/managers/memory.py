from __future__ import annotations

from typing import Any, Dict, List, Optional

from l6e_forge.memory.backends.base import IMemoryBackend
from l6e_forge.memory.managers.base import IMemoryManager
from l6e_forge.memory.embeddings.base import IEmbeddingProvider
from l6e_forge.memory.embeddings.mock import MockEmbeddingProvider
from l6e_forge.types.core import Message, ConversationID


from l6e_forge.memory.conversation.base import IConversationStore
from l6e_forge.types.memory import MemoryResult


class MemoryManager(IMemoryManager):
    def __init__(
        self,
        vector_store: Optional[IMemoryBackend] = None,
        embedder: IEmbeddingProvider | None = None,
        conversation_store: Optional[IConversationStore] = None,
    ) -> None:
        self._store = vector_store
        self._embedder = embedder or MockEmbeddingProvider()
        self._kv: Dict[str, Dict[str, Any]] = {}
        self._conversations: Dict[str, List[Message]] = {}
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._conversation_store = conversation_store

    async def store_vector(
        self,
        namespace: str,
        key: str,
        content: str,
        metadata: dict[str, Any] | None = None,
        *,
        collection: str | None = None,
    ) -> None:
        if self._store is None:
            raise ValueError("No vector store provided")
        emb = self._embedder.embed(content)
        await self._store.upsert(
            namespace, key, emb, content, collection or "default", metadata=metadata
        )

    async def search_vectors(
        self,
        namespace: str,
        query: str,
        collection: str | None = None,
        limit: int = 10,
    ) -> list[MemoryResult]:
        if self._store is None:
            raise ValueError("No vector store provided")
        q = self._embedder.embed(query)
        rows = await self._store.query(
            namespace, q, limit=limit, collection=collection or "default"
        )
        out: list[MemoryResult] = []
        for idx, (key, score, item) in enumerate(rows, start=1):
            out.append(
                MemoryResult(
                    content=item.content,
                    score=score,
                    metadata=item.metadata,
                    namespace=namespace,
                    key=key,
                    timestamp=None,  # type: ignore[arg-type]
                    embedding=None,
                    distance=None,
                    rank=idx,
                )
            )
        return out

    async def search_vectors_multi(
        self,
        namespaces: list[str] | list[tuple[str, str]],
        query: str,
        per_namespace_limit: int = 5,
        overall_limit: int | None = None,
    ) -> list[MemoryResult]:
        if self._store is None:
            raise ValueError("No vector store provided")
        q = self._embedder.embed(query)
        merged: list[MemoryResult] = []
        for entry in namespaces:
            if isinstance(entry, tuple):
                ns, col = entry
            else:
                ns, col = entry, "default"
            rows = await self._store.query(
                ns, q, limit=per_namespace_limit, collection=col
            )
            for _key, score, item in rows:
                merged.append(
                    MemoryResult(
                        content=item.content,
                        score=score,
                        metadata=item.metadata,
                        namespace=ns,
                        key=_key,
                        timestamp=None,  # type: ignore[arg-type]
                        embedding=None,
                        distance=None,
                        rank=0,
                    )
                )
        # Sort by score desc and assign rank
        merged.sort(
            key=lambda m: (m.score if m.score is not None else 0.0), reverse=True
        )
        if overall_limit is not None:
            merged = merged[:overall_limit]
        for i, m in enumerate(merged, start=1):
            m.rank = i
        return merged

    async def store_kv(self, namespace: str, key: str, value: Any) -> None:
        ns = self._kv.setdefault(namespace, {})
        ns[key] = value

    async def get_kv(self, namespace: str, key: str) -> Any:
        return self._kv.get(namespace, {}).get(key)

    async def delete_kv(self, namespace: str, key: str) -> None:
        self._kv.get(namespace, {}).pop(key, None)

    async def store_conversation(
        self, conversation_id: ConversationID, message: Message
    ) -> None:
        if self._conversation_store is not None:
            await self._conversation_store.store_message(conversation_id, message)
            return
        self._conversations.setdefault(str(conversation_id), []).append(message)

    async def get_conversation(
        self, conversation_id: ConversationID, limit: int = 50
    ) -> list[Message]:
        if self._conversation_store is not None:
            return await self._conversation_store.get_messages(conversation_id, limit)
        msgs = self._conversations.get(str(conversation_id), [])
        return msgs[-limit:]

    async def store_session(self, session_id: str, key: str, value: Any) -> None:
        self._sessions.setdefault(session_id, {})[key] = value

    async def get_session(self, session_id: str, key: str) -> Any:
        return self._sessions.get(session_id, {}).get(key)

    async def clear_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
