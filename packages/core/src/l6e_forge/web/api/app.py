from __future__ import annotations

import os
import uuid
from typing import Any

from fastapi import FastAPI, Response, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import os as _os

from l6e_forge.runtime.local import LocalRuntime
from l6e_forge.runtime.monitoring import get_monitoring
from l6e_forge.types.core import Message

import logging

logger = logging.getLogger(__name__)


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

    @app.get("/api/health")
    async def health() -> dict[str, str]:
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

            ws_path = workspace or os.environ.get("AF_WORKSPACE", "/workspace")
            if not ws_path:
                return {"error": "workspace not set"}

            ws = Path(ws_path).expanduser().resolve()
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
        workspace = str(
            payload.get("workspace", os.environ.get("AF_WORKSPACE", "/workspace"))
        )
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
            aid = (
                UUID(agent_id)
                if agent_id
                else (rt.get_agent_id_by_name(str(name)) if name else None)
            )
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
        # Start log removed to reduce duplicate noise; we log only the end
        workspace = str(
            payload.get("workspace", os.environ.get("AF_WORKSPACE", "/workspace"))
        )
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
        # Enforce UUID conversation ids. If client provides a non-UUID, ignore and generate a new one
        conversation_uuid: uuid.UUID
        if isinstance(incoming_conv, str) and incoming_conv.strip():
            try:
                conversation_uuid = uuid.UUID(incoming_conv.strip())
            except Exception:
                conversation_uuid = uuid.uuid4()
        else:
            conversation_uuid = uuid.uuid4()
        # Session can be client-provided; fallback to a new UUID
        if isinstance(incoming_sess, str) and incoming_sess.strip():
            session_uuid = incoming_sess.strip()
        else:
            session_uuid = str(uuid.uuid4())
        conversation_id = conversation_uuid
        # Idempotency: optional request_id from client; cache simple last result per (conversation_id, request_id)
        request_id = str(payload.get("request_id") or "").strip()
        _idem_key = f"{conversation_id}:{request_id}" if request_id else None
        # naive process-wide cache
        if not hasattr(chat, "_idem_cache"):
            setattr(chat, "_idem_cache", {})
        idem_cache: dict[str, Any] = getattr(chat, "_idem_cache")

        if _idem_key and _idem_key in idem_cache:
            return idem_cache[_idem_key]

        mon = get_monitoring()
        mon.add_chat_log(
            conversation_id=str(conversation_uuid), role="user", content=text
        )
        await mon.record_event("chat.message", {"direction": "in", "role": "user"})
        resp = await runtime.route_message(
            Message(role="user", content=text),
            target=aid,
            conversation_id=conversation_uuid,
            session_id=session_uuid,
        )
        print(f"/api/chat end agent_id={aid} content={resp.content!r}")
        mon.add_chat_log(
            conversation_id=str(conversation_uuid),
            role="assistant",
            content=resp.content,
            agent_id=str(aid),
        )
        await mon.record_event("chat.message", {"direction": "out", "agent": str(aid)})
        out = {
            "content": resp.content,
            "conversation_id": str(conversation_uuid),
            "session_id": session_uuid,
            "agent_id": str(aid),
        }
        if _idem_key:
            idem_cache[_idem_key] = out
        return out

    # Memory endpoints (MVP)
    @app.post("/api/memory/upsert")
    async def memory_upsert(payload: dict[str, Any]) -> dict[str, Any]:
        ns = str(payload.get("namespace", "default"))
        collection = str(payload.get("collection") or "").strip()
        key = str(payload.get("key"))
        content = str(payload.get("content", ""))
        metadata = payload.get("metadata") or {}
        if not key or not content:
            return {"error": "key and content are required"}
        mm = _runtime().get_memory_manager()
        await mm.store_vector(ns, key, content, metadata, collection=collection or None)
        return {"ok": True}

    @app.post("/api/memory/search")
    async def memory_search(payload: dict[str, Any]) -> dict[str, Any]:
        ns = str(payload.get("namespace", "default"))
        collection = str(payload.get("collection") or "").strip()
        query = str(payload.get("query", ""))
        limit = int(payload.get("limit", 5))
        if not query:
            return {"error": "query is required"}
        mm = _runtime().get_memory_manager()
        results = await mm.search_vectors(
            ns, query, limit=limit, collection=collection or None
        )
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

    # Serve monitor data directly under API namespace. Monitor service remains internal-only.
    @app.get("/api/perf")
    async def api_perf() -> dict[str, Any]:
        mon = get_monitoring()
        return mon.get_perf_summary()

    @app.get("/api/perf/by-agent")
    async def api_perf_by_agent() -> dict[str, Any]:
        mon = get_monitoring()
        return mon.get_perf_by_agent()

    @app.get("/api/chats")
    async def api_chats(limit: int = 200) -> list[dict[str, Any]]:
        mon = get_monitoring()
        return mon.get_chat_logs(limit)

    @app.websocket("/api/ws")
    async def ws_stream(ws: WebSocket) -> None:
        await ws.accept()
        mon = get_monitoring()
        # Try to subscribe to live monitor updates; fallback to polling if unsupported
        try:
            q = await mon.subscribe()  # type: ignore[attr-defined]
        except Exception:
            q = None
        # If remote monitor URL is configured, bridge its WebSocket directly
        remote_url = _os.environ.get("AF_MONITOR_URL", "").strip()
        bridge_task = None
        if not q and remote_url:
            logger.info(f"Bridging to remote monitor at {remote_url}")
            try:
                import websockets

                async def bridge_remote() -> None:
                    remote_ws = (
                        remote_url.replace("http://", "ws://")
                        .replace("https://", "wss://")
                        .rstrip("/")
                        + "/ws"
                    )
                    async with websockets.connect(remote_ws) as rws:
                        async for msg in rws:
                            try:
                                await ws.send_text(str(msg))
                            except Exception:
                                break
                    logger.info(f"Bridge to remote monitor at {remote_ws} closed")

                bridge_task = asyncio.create_task(bridge_remote())
            except Exception:
                bridge_task = None
        try:
            # Initial snapshot
            try:
                snapshot = {
                    "type": "snapshot",
                    "agents": mon.get_agent_status(),
                    "perf": mon.get_perf_summary(),
                }
                await ws.send_json(snapshot)
            except Exception:
                pass

            if q is not None:
                # Stream from monitor broadcasts; also send ping to keepalive
                while True:
                    try:
                        msg = await asyncio.wait_for(q.get(), timeout=30.0)  # type: ignore[arg-type]
                    except asyncio.TimeoutError:
                        await ws.send_json({"type": "ping"})
                        continue
                    try:
                        await ws.send_json(msg)  # type: ignore[arg-type]
                    except Exception:
                        break
            elif bridge_task is not None:
                # Wait on bridge task until closed
                try:
                    await bridge_task
                except Exception:
                    pass
            else:
                # Fallback: periodic polling and sending deltas
                while True:
                    try:
                        await ws.send_json(
                            {
                                "type": "metric",
                                "data": {
                                    "name": "response_time_ms",
                                    **mon.get_perf_summary(),
                                },
                            }
                        )
                        await asyncio.sleep(2.0)
                    except Exception:
                        break
        finally:
            try:
                if q is not None:
                    await mon.unsubscribe(q)  # type: ignore[attr-defined]
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
