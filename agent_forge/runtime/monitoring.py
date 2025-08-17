from __future__ import annotations

from typing import Optional

from agent_forge.monitor.base import IMonitoringService
from agent_forge.monitor.inmemory import InMemoryMonitoringService


_monitoring_singleton: Optional[IMonitoringService] = None


def get_monitoring() -> IMonitoringService:
    global _monitoring_singleton
    if _monitoring_singleton is None:
        _monitoring_singleton = InMemoryMonitoringService()
    return _monitoring_singleton


def set_monitoring(service: IMonitoringService) -> None:
    global _monitoring_singleton
    _monitoring_singleton = service


