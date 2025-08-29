from __future__ import annotations

from typing import Optional
import os

from l6e_forge.monitor.base import IMonitoringService
from l6e_forge.monitor.inmemory import InMemoryMonitoringService
from l6e_forge.monitor.remote import RemoteMonitoringService


_monitoring_singleton: Optional[IMonitoringService] = None


def get_monitoring() -> IMonitoringService:
    global _monitoring_singleton
    if _monitoring_singleton is None:
        base_url = os.environ.get("AF_MONITOR_URL", "").strip()
        if base_url:
            _monitoring_singleton = RemoteMonitoringService(base_url)
        else:
            _monitoring_singleton = InMemoryMonitoringService()
    return _monitoring_singleton


def set_monitoring(service: IMonitoringService) -> None:
    global _monitoring_singleton
    _monitoring_singleton = service
