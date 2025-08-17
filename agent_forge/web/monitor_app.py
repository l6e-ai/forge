from __future__ import annotations

import asyncio
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from agent_forge.monitor.base import IMonitoringService


def create_app(monitor: IMonitoringService) -> FastAPI:
    app = FastAPI(title="Agent Forge Monitor", version="0.1")

    # Static UI
    @app.get("/")
    async def index() -> HTMLResponse:
        return HTMLResponse(_INDEX_HTML)

    @app.get("/api/agents")
    async def agents() -> JSONResponse:
        return JSONResponse(monitor.get_agent_status())

    @app.get("/api/events")
    async def events() -> JSONResponse:
        return JSONResponse(monitor.get_recent_events(200))

    @app.get("/api/chats")
    async def chats() -> JSONResponse:
        return JSONResponse(monitor.get_chat_logs(200))

    @app.get("/api/perf")
    async def perf() -> JSONResponse:
        return JSONResponse(monitor.get_perf_summary())

    @app.websocket("/ws")
    async def websocket_endpoint(ws: WebSocket) -> None:
        await ws.accept()
        q = await monitor.subscribe()  # type: ignore[attr-defined]
        try:
            # Send initial snapshot
            await ws.send_json({"type": "snapshot", "agents": monitor.get_agent_status(), "perf": monitor.get_perf_summary()})
            while True:
                try:
                    msg = await asyncio.wait_for(q.get(), timeout=30.0)
                except asyncio.TimeoutError:
                    # Keep connection alive
                    await ws.send_json({"type": "ping"})
                    continue
                await ws.send_json(msg)  # type: ignore[arg-type]
        except WebSocketDisconnect:
            pass
        finally:
            try:
                await monitor.unsubscribe(q)  # type: ignore[attr-defined]
            except Exception:
                pass

    return app


_INDEX_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Agent Forge Monitor</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif; margin: 0; padding: 0; background: #0b0f14; color: #e6edf3; }
    header { position: sticky; top: 0; background: #0d1117; padding: 12px 16px; border-bottom: 1px solid #30363d; display: flex; align-items: center; justify-content: space-between; }
    h1 { font-size: 18px; margin: 0; }
    .grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; padding: 12px; }
    @media (max-width: 720px) { .grid { grid-template-columns: 1fr; } }
    .card { background: #0d1117; border: 1px solid #30363d; border-radius: 8px; padding: 12px; min-height: 120px; }
    .section-title { font-weight: 600; margin-bottom: 8px; color: #a5b1c2; }
    .agents-list { display: flex; flex-direction: column; gap: 6px; }
    .agent { display: flex; justify-content: space-between; align-items: center; padding: 8px; border: 1px solid #30363d; border-radius: 6px; }
    .status { font-size: 12px; padding: 2px 8px; border-radius: 999px; }
    .status.ready { background: #122b14; color: #3fb950; border: 1px solid #238636; }
    .status.offline { background: #2b1414; color: #f85149; border: 1px solid #da3633; }
    .logs { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 12px; }
    .log { border-bottom: 1px dashed #30363d; padding: 6px 0; }
    .flex { display: flex; gap: 12px; align-items: center; }
    .muted { color: #8b949e; }
  </style>
  <script>
    let ws;
    function connect() {
      const url = (location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + '/ws';
      ws = new WebSocket(url);
      ws.onmessage = (ev) => {
        const msg = JSON.parse(ev.data);
        if (msg.type === 'snapshot') {
          renderAgents(msg.agents);
          renderPerf(msg.perf);
          return;
        }
        if (msg.type === 'metric' && msg.data.name === 'response_time_ms') {
          fetch('/api/perf').then(r => r.json()).then(renderPerf);
        }
        if (msg.type === 'event') {
          if (msg.data.event_type === 'chat.message') {
            fetch('/api/chats').then(r => r.json()).then(renderChats);
          }
          if (msg.data.event_type === 'agent.registered' || msg.data.event_type === 'agent.unregistered') {
            fetch('/api/agents').then(r => r.json()).then(renderAgents);
          }
        }
      };
      ws.onclose = () => setTimeout(connect, 1000);
    }

    function renderAgents(agents) {
      const el = document.getElementById('agents');
      el.innerHTML = agents.map(a => `
        <div class="agent">
          <div class="flex">
            <strong>${a.name}</strong>
            <span class="muted">${a.agent_id.slice(0,8)}</span>
          </div>
          <span class="status ${a.status}">${a.status}</span>
        </div>
      `).join('');
    }

    function renderPerf(perf) {
      const el = document.getElementById('perf');
      el.innerHTML = `Avg: ${perf.avg_ms.toFixed(1)} ms • P95: ${perf.p95_ms.toFixed(1)} ms • Count: ${perf.count}`;
    }

    function renderChats(chats) {
      const el = document.getElementById('chats');
      el.innerHTML = chats.slice().reverse().map(c => `
        <div class="log">
          <span class="muted">${new Date(c.timestamp).toLocaleTimeString()}</span>
          <strong>[${c.role}]</strong> ${c.content}
        </div>
      `).join('');
    }

    async function loadInitial() {
      const [agents, perf, chats] = await Promise.all([
        fetch('/api/agents').then(r => r.json()),
        fetch('/api/perf').then(r => r.json()),
        fetch('/api/chats').then(r => r.json()),
      ]);
      renderAgents(agents);
      renderPerf(perf);
      renderChats(chats);
    }

    window.addEventListener('load', () => { connect(); loadInitial(); });
  </script>
</head>
<body>
  <header>
    <h1>Agent Forge Monitor</h1>
    <div id="perf" class="muted"></div>
  </header>
  <div class="grid">
    <div class="card">
      <div class="section-title">Active Agents</div>
      <div id="agents" class="agents-list"></div>
    </div>
    <div class="card">
      <div class="section-title">System Events</div>
      <div id="events" class="logs muted">Live via WS...</div>
    </div>
    <div class="card" style="grid-column: 1 / -1;">
      <div class="section-title">Chat Logs</div>
      <div id="chats" class="logs"></div>
    </div>
  </div>
</body>
</html>
"""


