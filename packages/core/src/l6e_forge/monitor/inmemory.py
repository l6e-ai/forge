from __future__ import annotations

import asyncio
import time
from collections import deque
from datetime import datetime
from typing import Any, Deque

from l6e_forge.monitor.base import IMonitoringService


class InMemoryMonitoringService(IMonitoringService):
    """Simple in-memory monitoring store with pub/sub for real-time updates.

    - Stores recent metrics and events in bounded deques to avoid unbounded memory use
    - Provides an asyncio.Queue-based broadcast channel for subscribers (websocket clients)
    - Tracks lightweight agent status and chat logs
    """

    def __init__(
        self,
        max_events: int = 2000,
        max_metrics_per_name: int = 1000,
        max_chats: int = 2000,
    ) -> None:
        self._events: Deque[dict[str, Any]] = deque(maxlen=max_events)
        self._metric_name_to_points: dict[str, Deque[dict[str, Any]]] = {}
        self._metric_name_to_points_max: int = max_metrics_per_name
        self._traces: dict[str, dict[str, Any]] = {}
        self._agent_status: dict[str, dict[str, Any]] = {}
        self._chat_logs: Deque[dict[str, Any]] = deque(maxlen=max_chats)

        # Broadcast channel for real-time stream
        self._subscribers: set[asyncio.Queue] = set()
        self._lock = asyncio.Lock()

    # ---- Public API (IMonitoringService) ----
    async def record_metric(
        self, name: str, value: float, tags: dict[str, str] | None = None
    ) -> None:
        point = {
            "name": name,
            "value": value,
            "tags": tags or {},
            "timestamp": datetime.now().isoformat(),
        }
        if name not in self._metric_name_to_points:
            self._metric_name_to_points[name] = deque(
                maxlen=self._metric_name_to_points_max
            )
        self._metric_name_to_points[name].append(point)
        await self._broadcast({"type": "metric", "data": point})

    async def record_event(self, name: str, data: dict[str, Any]) -> None:
        evt = {
            "event_type": name,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }
        self._events.append(evt)
        await self._broadcast({"type": "event", "data": evt})

    def get_metrics(
        self, name: str, time_range: tuple[datetime, datetime] | None = None
    ) -> list[dict[str, Any]]:
        series = list(self._metric_name_to_points.get(name, []))
        if time_range is None:
            return series
        start, end = time_range

        def _isin(p: dict[str, Any]) -> bool:
            try:
                ts = datetime.fromisoformat(str(p.get("timestamp")))
            except Exception:
                return False
            return start <= ts <= end

        return [p for p in series if _isin(p)]

    async def start_trace(self, trace_name: str) -> str:
        trace_id = f"trace_{int(time.time() * 1000)}"
        self._traces[trace_id] = {
            "trace_name": trace_name,
            "started_at": datetime.now().isoformat(),
            "steps": [],
        }
        await self._broadcast(
            {
                "type": "trace_start",
                "data": {"trace_id": trace_id, "trace_name": trace_name},
            }
        )
        return trace_id

    async def end_trace(self, trace_id: str) -> None:
        trace = self._traces.get(trace_id)
        if trace is not None:
            trace["ended_at"] = datetime.now().isoformat()
            await self._broadcast({"type": "trace_end", "data": {"trace_id": trace_id}})

    # ---- Convenience helpers for UI ----
    def get_recent_events(self, limit: int = 200) -> list[dict[str, Any]]:
        return list(self._events)[-limit:]

    def get_agent_status(self) -> list[dict[str, Any]]:
        return list(self._agent_status.values())

    def set_agent_status(
        self,
        agent_id: str,
        name: str,
        status: str,
        config: dict[str, Any] | None = None,
    ) -> None:
        self._agent_status[agent_id] = {
            "agent_id": agent_id,
            "name": name,
            "status": status,
            "config": config or {},
            "last_seen": datetime.now().isoformat(),
        }

    def remove_agent(self, agent_id: str) -> None:
        self._agent_status.pop(agent_id, None)

    def add_chat_log(
        self, conversation_id: str, role: str, content: str, agent_id: str | None = None
    ) -> None:
        entry = {
            "conversation_id": str(conversation_id),
            "role": role,
            "content": content,
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
        }
        self._chat_logs.append(entry)

    def get_chat_logs(self, limit: int = 200) -> list[dict[str, Any]]:
        return list(self._chat_logs)[-limit:]

    def get_perf_summary(self) -> dict[str, Any]:
        points = list(self._metric_name_to_points.get("response_time_ms", []))
        values = [float(p.get("value", 0.0)) for p in points]
        if not values:
            return {"avg_ms": 0.0, "p95_ms": 0.0, "count": 0}
        sorted_vals = sorted(values)
        p95_index = max(0, int(len(sorted_vals) * 0.95) - 1)
        return {
            "avg_ms": sum(values) / len(values),
            "p95_ms": sorted_vals[p95_index],
            "count": len(values),
        }

    def get_perf_by_agent(self) -> dict[str, Any]:
        # Group response_time_ms by agent tag
        points = list(self._metric_name_to_points.get("response_time_ms", []))
        buckets: dict[str, list[float]] = {}
        for p in points:
            try:
                tags = p.get("tags") or {}
                agent_id = str(tags.get("agent") or "unknown")
                buckets.setdefault(agent_id, []).append(float(p.get("value", 0.0)))
            except Exception:
                continue
        out: dict[str, dict[str, Any]] = {}
        for agent_id, values in buckets.items():
            if not values:
                continue
            sorted_vals = sorted(values)
            p95_index = max(0, int(len(sorted_vals) * 0.95) - 1)
            out[agent_id] = {
                "avg_ms": sum(values) / len(values),
                "p95_ms": sorted_vals[p95_index],
                "count": len(values),
            }
        return out

    # ---- Subscription management ----
    async def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        async with self._lock:
            self._subscribers.add(q)
        return q

    async def unsubscribe(self, q: asyncio.Queue) -> None:
        async with self._lock:
            self._subscribers.discard(q)

    async def _broadcast(self, message: dict[str, Any]) -> None:
        # Best effort broadcast; drop if queue is full
        async with self._lock:
            subscribers = list(self._subscribers)
        for q in subscribers:
            try:
                q.put_nowait(message)
            except Exception:
                # Slow or closed subscriber; ignore
                pass
