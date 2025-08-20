from __future__ import annotations

from pathlib import Path
import importlib.util
import sys
import uuid
from typing import Callable, Any
import os

from agent_forge.types.core import AgentID, AgentResponse, Message
from agent_forge.types.agent import AgentSpec
from agent_forge.runtime.monitoring import get_monitoring

# Type-only import to avoid circulars
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from agent_forge.core.agents.base import IAgent
    from agent_forge.events.bus.base import IEventBus
    from agent_forge.memory.managers.base import IMemoryManager
    from agent_forge.models.managers.base import IModelManager
    from agent_forge.tools.registry.base import IToolRegistry


class LocalRuntime:
    """Minimal local runtime for MVP.

    Responsibilities implemented now:
    - Register an agent from its directory (expects agent.py with class Agent)
    - Keep a registry of loaded agents by UUID
    - Route a message to a target agent (or the first registered)
    - List agents (empty specs for now)

    Unimplemented (stubs only): event bus, memory manager, model manager, tool registry.
    """

    def __init__(self) -> None:
        self._id_to_agent: dict[AgentID, "IAgent"] = {}
        self._id_to_name: dict[AgentID, str] = {}
        self._name_to_id: dict[str, AgentID] = {}
        self._model_manager = None
        self._agent_configs: dict[AgentID, dict[str, Any]] = {}
        self._agent_paths: dict[AgentID, Path] = {}
        self._tool_registry = None

    # Agent management
    async def register_agent(self, agent_path: Path) -> AgentID:
        agent_dir = Path(agent_path).resolve()
        agent_py = agent_dir / "agent.py"
        if not agent_py.exists():
            raise FileNotFoundError(f"agent.py not found at {agent_py}")

        agent_name = agent_dir.name
        module_name = f"agent_forge_runtime.{agent_name}"
        spec = importlib.util.spec_from_file_location(module_name, agent_py)
        if not spec or not spec.loader:
            raise RuntimeError(f"Unable to load module for agent: {agent_name}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        if not hasattr(module, "Agent"):
            raise AttributeError(f"Agent class not found in {agent_py}")

        agent_instance: IAgent = getattr(module, "Agent")()  # type: ignore[name-defined]
        # Load agent config if present
        config_data: dict[str, Any] = {}
        try:
            from agent_forge.config_managers.toml import TomlConfigManager

            cfg_mgr = TomlConfigManager()
            cfg_path = agent_dir / "config.toml"
            if cfg_path.exists():
                config_data = await cfg_mgr.load_config(cfg_path)
        except Exception:
            config_data = {}

        # Best-effort initialize and configure
        try:
            init_fn = getattr(agent_instance, "initialize", None)
            if callable(init_fn):
                await init_fn(self)  # type: ignore[arg-type]
            cfg_fn = getattr(agent_instance, "configure", None)
            if callable(cfg_fn) and config_data:
                await cfg_fn(config_data)  # type: ignore[arg-type]
        except Exception:
            # Do not fail registration on init errors in MVP
            pass

        agent_id = uuid.uuid4()
        self._id_to_agent[agent_id] = agent_instance
        self._id_to_name[agent_id] = agent_name
        self._name_to_id[agent_name] = agent_id
        self._agent_configs[agent_id] = config_data
        self._agent_paths[agent_id] = agent_dir
        # Assign default toolkit on first use
        try:
            _ = self.get_tool_registry()
            from agent_forge.tools.filesystem import FilesystemTool
            from agent_forge.tools.terminal import TerminalTool
            from agent_forge.tools.web import WebFetchTool
            from agent_forge.tools.code import CodeUtilsTool

            fs_id = self._tool_registry.register_tool(FilesystemTool())
            term_id = self._tool_registry.register_tool(TerminalTool())
            web_id = self._tool_registry.register_tool(WebFetchTool())
            code_id = self._tool_registry.register_tool(CodeUtilsTool())
            self._tool_registry.assign_tools_to_agent(agent_id, [fs_id, term_id, web_id, code_id])
        except Exception:
            # Best-effort only in MVP
            pass
        # Update monitoring
        try:
            mon = get_monitoring()
            mon.set_agent_status(str(agent_id), agent_name, status="ready", config=config_data)
            await mon.record_event("agent.registered", {"agent_id": str(agent_id), "name": agent_name})
        except Exception:
            pass
        return agent_id

    async def unregister_agent(self, agent_id: AgentID) -> None:
        name = self._id_to_name.pop(agent_id, None)
        self._id_to_agent.pop(agent_id, None)
        if name:
            self._name_to_id.pop(name, None)
        try:
            mon = get_monitoring()
            mon.remove_agent(str(agent_id))
            await mon.record_event("agent.unregistered", {"agent_id": str(agent_id), "name": name})
        except Exception:
            pass

    async def reload_agent(self, agent_id: AgentID) -> None:
        # For MVP, re-register by name
        name = self._id_to_name.get(agent_id)
        if not name:
            return
        # Assume same path structure under current working directory is not tracked; skip for now
        # A future implementation should persist the path
        pass

    async def get_agent(self, agent_id: AgentID):  # -> IAgent
        return self._id_to_agent[agent_id]

    def get_agent_config(self, agent_id: AgentID) -> dict[str, Any]:
        return self._agent_configs.get(agent_id, {})

    async def list_agents(self) -> list[AgentSpec]:
        # Return an empty list of specs for now; will be filled later
        return []

    # Message routing
    async def route_message(
        self,
        message: Message,
        target: AgentID | None = None,
        conversation_id: str | None = None,
        session_id: str | None = None,
    ) -> AgentResponse:
        agent: "IAgent" | None = None
        if target is not None:
            agent = self._id_to_agent.get(target)
        else:
            agent = next(iter(self._id_to_agent.values()), None)
        if agent is None:
            raise RuntimeError("No registered agents to route message to")
        # Minimal context
        from agent_forge.types.core import AgentContext  # local import to avoid cycles

        ctx = AgentContext(conversation_id=conversation_id or "local", session_id=session_id or "local")
        # Log request
        try:
            mon = get_monitoring()
            mon.add_chat_log(conversation_id=ctx.conversation_id or "local", role=message.role, content=message.content)
            await mon.record_event("chat.message", {"direction": "in", "role": message.role})
        except Exception:
            pass
        import time as _time
        _start = _time.perf_counter()
        resp = await agent.handle_message(message, ctx)
        _elapsed_ms = (_time.perf_counter() - _start) * 1000.0
        # Log response
        try:
            mon = get_monitoring()
            mon.add_chat_log(conversation_id=ctx.conversation_id or "local", role="assistant", content=resp.content, agent_id=resp.agent_id)
            await mon.record_metric("response_time_ms", _elapsed_ms, tags={"agent": resp.agent_id})
            await mon.record_event("chat.message", {"direction": "out", "agent": resp.agent_id})
        except Exception:
            pass
        return resp

    async def broadcast_message(self, message: Message, filter_fn: Callable | None = None) -> list[AgentResponse]:
        results: list[AgentResponse] = []
        for agent in self._id_to_agent.values():
            if filter_fn and not filter_fn(agent):  # type: ignore[arg-type]
                continue
            from agent_forge.types.core import AgentContext  # local import to avoid cycles

            ctx = AgentContext(conversation_id="local", session_id="local")
            results.append(await agent.handle_message(message, ctx))
        return results

    # Resource management (stubs)
    def get_memory_manager(self):  # -> IMemoryManager
        raise NotImplementedError

    def get_model_manager(self):  # -> IModelManager
        if self._model_manager is None:
            # Use provider registry with endpoints from forge.toml (workspace root is parent of agents dir)
            from agent_forge.models.providers.registry import load_endpoints_from_config, get_manager

            workspace_root = Path.cwd()
            _default_provider, endpoints = load_endpoints_from_config(workspace_root)
            provider = (os.environ.get("AF_DEFAULT_PROVIDER") or _default_provider or "ollama")
            self._model_manager = get_manager(provider, endpoints)
        return self._model_manager

    def get_tool_registry(self):  # -> IToolRegistry
        if self._tool_registry is None:
            from agent_forge.tools.registry.inmemory import InMemoryToolRegistry

            self._tool_registry = InMemoryToolRegistry()
        return self._tool_registry

    def get_event_bus(self):  # -> IEventBus
        raise NotImplementedError

    # Development support (stubs)
    async def start_dev_mode(self, port: int = 8123) -> None:
        return None

    async def enable_hot_reload(self, watch_paths: list[Path]) -> None:
        return None


