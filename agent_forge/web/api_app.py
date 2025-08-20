from __future__ import annotations

import os
import uuid
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agent_forge.runtime.local import LocalRuntime
from agent_forge.runtime.monitoring import get_monitoring
from agent_forge.types.core import Message, AgentContext


def create_app() -> FastAPI:
    app = FastAPI(title="Agent Forge API", version="0.1")

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

    @app.post("/chat")
    async def chat(payload: dict[str, Any]) -> dict[str, Any]:
        agent_name = str(payload.get("agent", "default"))
        text = str(payload.get("message", "")).strip()
        workspace = str(payload.get("workspace", os.environ.get("AF_WORKSPACE", "/workspace")))
        if not text:
            return {"error": "empty message"}

        runtime = LocalRuntime()
        # The agent directories are expected under <workspace>/agents/<agent_name>
        from pathlib import Path
        agent_dir = Path(workspace).expanduser().resolve() / "agents" / agent_name
        if not (agent_dir / "agent.py").exists():
            return {"error": f"agent not found: {agent_name}"}

        agent_id = await runtime.register_agent(agent_dir)
        try:
            session_uuid = str(uuid.uuid4())
            conversation_id = f"{agent_name}:{session_uuid}"
            ctx = AgentContext(conversation_id=conversation_id, session_id=session_uuid)
            mon = get_monitoring()
            mon.add_chat_log(conversation_id=conversation_id, role="user", content=text)
            await mon.record_event("chat.message", {"direction": "in", "role": "user"})
            resp = await runtime.route_message(Message(role="user", content=text), target=agent_id, conversation_id=conversation_id, session_id=session_uuid)
            mon.add_chat_log(conversation_id=conversation_id, role="assistant", content=resp.content, agent_id=str(agent_id))
            await mon.record_event("chat.message", {"direction": "out", "agent": str(agent_id)})
            return {"content": resp.content, "conversation_id": conversation_id, "agent_id": str(agent_id)}
        finally:
            try:
                await runtime.unregister_agent(agent_id)
            except Exception:
                pass

    return app


