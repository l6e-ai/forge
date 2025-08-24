from __future__ import annotations

from typing import Any, Dict, List

from l6e_forge.memory.managers.base import IMemoryManager
from l6e_forge.memory.embeddings.base import IEmbeddingProvider
from l6e_forge.memory.embeddings.mock import MockEmbeddingProvider
from l6e_forge.types.core import Message
from l6e_forge.types.memory import MemoryResult


class InMemoryMemoryManager(IMemoryManager):
    def __init__(self, vector_store, embedder: IEmbeddingProvider | None = None) -> None:
        self._store = vector_store
        self._embedder = embedder or MockEmbeddingProvider()
        self._kv: Dict[str, Dict[str, Any]] = {}
        self._conversations: Dict[str, List[Message]] = {}
        self._sessions: Dict[str, Dict[str, Any]] = {}

    async def store_vector(self, namespace: str, key: str, content: str, metadata: dict[str, Any] | None = None) -> None:
        emb = self._embedder.embed(content)
        await self._store.upsert(namespace, key, emb, content, metadata)

    async def search_vectors(self, namespace: str, query: str, limit: int = 10) -> list[MemoryResult]:
        q = self._embedder.embed(query)
        rows = await self._store.query(namespace, q, limit=limit)
        out: list[MemoryResult] = []
        for idx, (key, score, item) in enumerate(rows, start=1):
            out.append(MemoryResult(
                content=item.content,
                score=score,
                metadata=item.metadata,
                namespace=namespace,
                key=key,
                timestamp=None,  # type: ignore[arg-type]
                embedding=None,
                distance=None,
                rank=idx,
            ))
        return out

    async def store_kv(self, namespace: str, key: str, value: Any) -> None:
        ns = self._kv.setdefault(namespace, {})
        ns[key] = value

    async def get_kv(self, namespace: str, key: str) -> Any:
        return self._kv.get(namespace, {}).get(key)

    async def delete_kv(self, namespace: str, key: str) -> None:
        self._kv.get(namespace, {}).pop(key, None)

    async def store_conversation(self, conversation_id: str, message: Message) -> None:
        self._conversations.setdefault(conversation_id, []).append(message)

    async def get_conversation(self, conversation_id: str, limit: int = 50) -> list[Message]:
        msgs = self._conversations.get(conversation_id, [])
        return msgs[-limit:]

    async def store_session(self, session_id: str, key: str, value: Any) -> None:
        self._sessions.setdefault(session_id, {})[key] = value

    async def get_session(self, session_id: str, key: str) -> Any:
        return self._sessions.get(session_id, {}).get(key)

    async def clear_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)


