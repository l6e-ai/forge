from __future__ import annotations

import os

from l6e_forge.runtime.monitoring import get_monitoring
from .app import create_app


# TODO add routers for layered API

_PORT = int(
    os.environ.get("MONITOR_PORT", "8321")
)  # Not used directly but helpful context

# Uvicorn entrypoint:
app = create_app(get_monitoring())
