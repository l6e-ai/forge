from __future__ import annotations

import os
import uuid
from typing import Any

from fastapi import FastAPI, Request, Response, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from l6e_forge.runtime.local import LocalRuntime
from l6e_forge.runtime.monitoring import get_monitoring
from l6e_forge.types.core import Message, AgentContext


_runtime_singleton: LocalRuntime | None = None


def _runtime() -> LocalRuntime:
    global _runtime_singleton
    if _runtime_singleton is None:
        _runtime_singleton = LocalRuntime()
    return _runtime_singleton


def create_app() -> FastAPI:
    app = FastAPI(title="l6e forge API", version="0.1")

    # CORS for local dev and compose usage
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"ok": "true"}

    @app.get("/agents")
    @app.get("/api/agents")
    async def list_agents(workspace: str | None = None) -> dict[str, Any]:
        # Active: registered in runtime
        active = _runtime().list_registered()
        print(f"active: {active}")
        # Discover: list directories in workspace/agents
        discovered: list[str] = []
        try:
            from pathlib import Path
            ws = Path(workspace or os.environ.get("AF_WORKSPACE", "/workspace")).expanduser().resolve()
            agents_dir = ws / "agents"
            if agents_dir.exists():
                for p in agents_dir.iterdir():
                    print(f"p: {p}")
                    if p.is_dir():
                        discovered.append(p.name)
        except Exception:
            pass
        return {"active": active, "discovered": sorted(list(set(discovered)))}

    @app.post("/agents/start")
    @app.post("/api/agents/start")
    async def start_agent(payload: dict[str, Any]) -> dict[str, Any]:
        agent_name = str(payload.get("name"))
        workspace = str(payload.get("workspace", os.environ.get("AF_WORKSPACE", "/workspace")))
        from pathlib import Path
        agent_dir = Path(workspace).expanduser().resolve() / "agents" / agent_name
        agent_id = await _runtime().register_agent(agent_dir)
        return {"agent_id": str(agent_id), "name": agent_name}

    @app.post("/agents/stop")
    @app.post("/api/agents/stop")
    async def stop_agent(payload: dict[str, Any]) -> dict[str, Any]:
        agent_id = str(payload.get("agent_id"))
        name = payload.get("name")
        rt = _runtime()
        from uuid import UUID
        try:
            aid = UUID(agent_id) if agent_id else (rt.get_agent_id_by_name(str(name)) if name else None)
        except Exception:
            aid = None
        if aid is None:
            return {"error": "invalid agent reference"}
        await rt.unregister_agent(aid)
        return {"ok": True}

    @app.post("/chat")
    @app.post("/api/chat")
    async def chat(payload: dict[str, Any]) -> dict[str, Any]:
        agent_name = str(payload.get("agent", "default"))
        text = str(payload.get("message", "")).strip()
        print(f"/api/chat start agent={agent_name} text={text!r}")
        workspace = str(payload.get("workspace", os.environ.get("AF_WORKSPACE", "/workspace")))
        if not text:
            return {"error": "empty message"}

        runtime = _runtime()
        # The agent directories are expected under <workspace>/agents/<agent_name>
        from pathlib import Path
        agent_dir = Path(workspace).expanduser().resolve() / "agents" / agent_name
        if not (agent_dir / "agent.py").exists():
            return {"error": f"agent not found: {agent_name}"}

        # Ensure agent is started if not yet registered
        aid = runtime.get_agent_id_by_name(agent_name)
        if aid is None:
            aid = await runtime.register_agent(agent_dir)
        # Support persistent conversations via optional conversation_id and session_id
        incoming_conv = payload.get("conversation_id")
        incoming_sess = payload.get("session_id")
        if isinstance(incoming_conv, str) and incoming_conv.strip():
            conversation_id = incoming_conv.strip()
            if isinstance(incoming_sess, str) and incoming_sess.strip():
                session_uuid = incoming_sess.strip()
            else:
                # Derive session from conversation suffix if format is agent:session
                parts = conversation_id.split(":")
                session_uuid = parts[-1] if len(parts) > 1 and parts[-1] else str(uuid.uuid4())
        else:
            session_uuid = str(uuid.uuid4())
            conversation_id = f"{agent_name}:{session_uuid}"
        ctx = AgentContext(conversation_id=conversation_id, session_id=session_uuid)
        mon = get_monitoring()
        mon.add_chat_log(conversation_id=conversation_id, role="user", content=text)
        await mon.record_event("chat.message", {"direction": "in", "role": "user"})
        resp = await runtime.route_message(Message(role="user", content=text), target=aid, conversation_id=conversation_id, session_id=session_uuid)
        print(f"/api/chat end agent_id={aid} content={resp.content!r}")
        mon.add_chat_log(conversation_id=conversation_id, role="assistant", content=resp.content, agent_id=str(aid))
        await mon.record_event("chat.message", {"direction": "out", "agent": str(aid)})
        return {"content": resp.content, "conversation_id": conversation_id, "session_id": session_uuid, "agent_id": str(aid)}

    # Memory endpoints (MVP)
    @app.post("/api/memory/upsert")
    async def memory_upsert(payload: dict[str, Any]) -> dict[str, Any]:
        ns = str(payload.get("namespace", "default"))
        key = str(payload.get("key"))
        content = str(payload.get("content", ""))
        metadata = payload.get("metadata") or {}
        if not key or not content:
            return {"error": "key and content are required"}
        mm = _runtime().get_memory_manager()
        await mm.store_vector(ns, key, content, metadata)
        return {"ok": True}

    @app.post("/api/memory/search")
    async def memory_search(payload: dict[str, Any]) -> dict[str, Any]:
        ns = str(payload.get("namespace", "default"))
        query = str(payload.get("query", ""))
        limit = int(payload.get("limit", 5))
        if not query:
            return {"error": "query is required"}
        mm = _runtime().get_memory_manager()
        results = await mm.search_vectors(ns, query, limit=limit)
        out = [
            {
                "namespace": r.namespace,
                "key": r.key,
                "score": r.score,
                "content": r.content,
                "metadata": r.metadata,
                "rank": r.rank,
            }
            for r in results
        ]
        return {"results": out}

    # Lightweight HTTP proxy to Monitor for production (mirrors dev Vite proxy)
    try:
        import httpx

        async def _proxy_monitor(request: Request) -> Response:
            monitor = os.environ.get("AF_MONITOR_URL", "http://localhost:8321").rstrip("/")
            path = request.path_params.get("path", "")
            target = f"{monitor}/api/{path}"
            method = request.method.upper()
            headers = dict(request.headers)
            headers.pop("host", None)
            body = await request.body()
            async with httpx.AsyncClient(timeout=None) as client:
                resp = await client.request(method, target, headers=headers, content=body)
                return Response(content=resp.content, status_code=resp.status_code, headers={k: v for k, v in resp.headers.items() if k.lower() not in {"content-encoding", "transfer-encoding", "connection"}})

        app.add_api_route("/monitor/api/{path:path}", _proxy_monitor, methods=["GET", "POST", "PUT", "PATCH", "DELETE"])  # type: ignore[arg-type]

        async def _proxy_monitor_ingest(request: Request) -> Response:
            monitor = os.environ.get("AF_MONITOR_URL", "http://localhost:8321").rstrip("/")
            path = request.path_params.get("path", "")
            target = f"{monitor}/ingest/{path}"
            method = request.method.upper()
            headers = dict(request.headers)
            headers.pop("host", None)
            body = await request.body()
            async with httpx.AsyncClient(timeout=None) as client:
                resp = await client.request(method, target, headers=headers, content=body)
                return Response(content=resp.content, status_code=resp.status_code, headers={k: v for k, v in resp.headers.items() if k.lower() not in {"content-encoding", "transfer-encoding", "connection"}})

        app.add_api_route("/monitor/ingest/{path:path}", _proxy_monitor_ingest, methods=["GET", "POST", "PUT", "PATCH", "DELETE"])  # type: ignore[arg-type]
    except Exception:
        pass

    # WebSocket proxy to Monitor
    try:
        import asyncio
        import websockets

        @app.websocket("/monitor/ws")
        async def monitor_ws_proxy(client_ws: WebSocket) -> None:
            await client_ws.accept()
            monitor = os.environ.get("AF_MONITOR_URL", "http://localhost:8321").rstrip("/")
            monitor_ws = monitor.replace("http://", "ws://").replace("https://", "wss://") + "/ws"
            async with websockets.connect(monitor_ws) as server_ws:
                async def _c2s() -> None:
                    try:
                        while True:
                            data = await client_ws.receive_text()
                            await server_ws.send(data)
                    except Exception:
                        try:
                            await server_ws.close()
                        except Exception:
                            pass

                async def _s2c() -> None:
                    try:
                        async for msg in server_ws:
                            await client_ws.send_text(msg)
                    except Exception:
                        try:
                            await client_ws.close()
                        except Exception:
                            pass

                await asyncio.gather(_c2s(), _s2c())
    except Exception:
        pass

    # Mount optional static UI at /ui (not / to avoid WS conflicts). Place assets in AF_UI_DIR or /app/static/ui
    try:
        ui_dir = os.environ.get("AF_UI_DIR", "/app/static/ui")
        if os.path.isdir(ui_dir):
            app.mount("/ui", StaticFiles(directory=ui_dir, html=True), name="ui")

            @app.get("/")
            async def root_index() -> Response:
                # Redirect to /ui/ index.html
                from fastapi.responses import RedirectResponse
                return RedirectResponse(url="/ui/")
    except Exception:
        pass

    return app


