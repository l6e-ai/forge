from __future__ import annotations

import os

from agent_forge.runtime.monitoring import get_monitoring
from agent_forge.web.monitor_app import create_app


_PORT = int(os.environ.get("MONITOR_PORT", "8321"))  # Not used directly but helpful context

# Uvicorn entrypoint:
app = create_app(get_monitoring())


