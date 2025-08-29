from typing import Any, Protocol
from datetime import datetime


class IMonitoringService(Protocol):
    """Monitoring service interface.

    This protocol defines both the ingest (write) API and the minimal read API
    required by the UI/API to display monitoring data.
    """

    # --- Ingest/write API ---
    async def record_metric(
        self, name: str, value: float, tags: dict[str, str] | None = None
    ) -> None:
        """Record a metric value."""
        ...

    async def record_event(self, name: str, data: dict[str, Any]) -> None:
        """Record an event with arbitrary data."""
        ...

    def set_agent_status(
        self,
        agent_id: str,
        name: str,
        status: str,
        config: dict[str, Any] | None = None,
    ) -> None:
        """Upsert lightweight agent status."""
        ...

    def remove_agent(self, agent_id: str) -> None:
        """Remove an agent from the status store."""
        ...

    def add_chat_log(
        self, conversation_id: str, role: str, content: str, agent_id: str | None = None
    ) -> None:
        """Append a chat log entry."""
        ...

    async def start_trace(self, trace_name: str) -> str:
        """Start a new trace and return trace ID."""
        ...

    async def end_trace(self, trace_id: str) -> None:
        """End a trace."""
        ...

    # --- Read API ---
    def get_metrics(
        self, name: str, time_range: tuple[datetime, datetime] | None = None
    ) -> list[dict[str, Any]]:
        """Get metric values for a time range."""
        ...

    def get_recent_events(self, limit: int = 200) -> list[dict[str, Any]]:
        """Return recent events for dashboards."""
        ...

    def get_agent_status(self) -> list[dict[str, Any]]:
        """Return current agent status snapshot."""
        ...

    def get_chat_logs(self, limit: int = 200) -> list[dict[str, Any]]:
        """Return recent chat logs."""
        ...

    def get_perf_summary(self) -> dict[str, Any]:
        """Return a small performance summary (avg, p95, count)."""
        ...

    def get_perf_by_agent(self) -> dict[str, dict[str, Any]]:
        """Return performance summary grouped by agent id: {agent_id: {avg_ms,p95_ms,count}}"""
        ...

    # --- Streaming/subscription API (optional) ---
    async def subscribe(self):  # -> asyncio.Queue
        """Subscribe to live updates. May not be supported by remote implementations."""
        ...

    async def unsubscribe(self, q) -> None:  # q: asyncio.Queue
        """Unsubscribe from live updates. May not be supported by remote implementations."""
        ...
