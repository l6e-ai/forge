from typing import Any, Protocol
from datetime import datetime


class IMonitoringService(Protocol):
    """Monitoring service interface"""
    
    async def record_metric(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        """Record a metric value"""
        ...
    
    async def record_event(self, name: str, data: dict[str, Any]) -> None:
        """Record an event"""
        ...
    
    def get_metrics(self, name: str, time_range: tuple[datetime, datetime] | None = None) -> list[dict[str, Any]]:
        """Get metric values for a time range"""
        ...
    
    async def start_trace(self, trace_name: str) -> str:
        """Start a new trace and return trace ID"""
        ...
    
    async def end_trace(self, trace_id: str) -> None:
        """End a trace"""
        ...
