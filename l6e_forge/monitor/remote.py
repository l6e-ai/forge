from __future__ import annotations

from typing import Any, Optional

import httpx

from l6e_forge.monitor.base import IMonitoringService


class RemoteMonitoringService(IMonitoringService):
    """HTTP client that forwards monitoring calls to a remote monitor server.

    The server is expected to be an instance of the l6e forge monitor app
    exposing the ingestion endpoints under /ingest/*.
    """

    def __init__(self, base_url: str, timeout_seconds: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    # --- IMonitoringService methods ---
    async def record_metric(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        await self._post("/ingest/metric", {"name": name, "value": value, "tags": tags or {}})

    async def record_event(self, name: str, data: dict[str, Any]) -> None:
        await self._post("/ingest/event", {"name": name, "data": data})

    def get_metrics(self, name: str, time_range: tuple[Any, Any] | None = None) -> list[dict[str, Any]]:  # type: ignore[override]
        # Not retrieved from remote for now
        return []

    async def start_trace(self, trace_name: str) -> str:
        resp = await self._post("/ingest/trace/start", {"trace_name": trace_name})
        try:
            return str((resp or {}).get("trace_id", ""))
        except Exception:
            return ""

    async def end_trace(self, trace_id: str) -> None:
        await self._post("/ingest/trace/end", {"trace_id": trace_id})

    # --- Extended helpers used by LocalRuntime ---
    def set_agent_status(self, agent_id: str, name: str, status: str, config: dict[str, Any] | None = None) -> None:  # noqa: D401
        # Execute synchronously to ensure registration updates land even if event loop ends
        self._post_sync("/ingest/agent/status", {"agent_id": agent_id, "name": name, "status": status, "config": config or {}})

    def remove_agent(self, agent_id: str) -> None:  # noqa: D401
        self._post_sync("/ingest/agent/remove", {"agent_id": agent_id})

    def add_chat_log(self, conversation_id: str, role: str, content: str, agent_id: str | None = None) -> None:  # noqa: D401
        self._post_sync("/ingest/chat", {"conversation_id": conversation_id, "role": role, "content": content, "agent_id": agent_id})

    # --- HTTP helper ---
    async def _post(self, path: str, json: dict[str, Any]) -> Optional[dict[str, Any]]:
        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                r = await client.post(url, json=json)
                r.raise_for_status()
                if r.headers.get("content-type", "").startswith("application/json"):
                    return r.json()
                return None
        except Exception:
            # Best-effort: swallow errors in MVP
            return None

    def _post_sync(self, path: str, json: dict[str, Any]) -> Optional[dict[str, Any]]:
        url = f"{self.base_url}{path}"
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                r = client.post(url, json=json)
                r.raise_for_status()
                if r.headers.get("content-type", "").startswith("application/json"):
                    return r.json()
                return None
        except Exception:
            return None


