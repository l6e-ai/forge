from __future__ import annotations

from pathlib import Path
import importlib.util
import sys
import uuid
from typing import Callable, Any
import os

from l6e_forge.types.core import AgentID, AgentResponse, Message, ConversationID
from l6e_forge.types.agent import AgentSpec
from l6e_forge.runtime.monitoring import get_monitoring
from l6e_forge.logging import get_logger

# Type-only import to avoid circulars
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from l6e_forge.core.agents.base import IAgent

logger = get_logger()


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
        self._memory_manager = None
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
        module_name = f"l6e_forge_runtime.{agent_name}"
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
            from l6e_forge.config_managers.toml import TomlConfigManager

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
            from l6e_forge.tools.filesystem import FilesystemTool
            from l6e_forge.tools.terminal import TerminalTool
            from l6e_forge.tools.web import WebFetchTool
            from l6e_forge.tools.code import CodeUtilsTool

            if self._tool_registry is not None:
                fs_id = self._tool_registry.register_tool(FilesystemTool())
                term_id = self._tool_registry.register_tool(TerminalTool())
                web_id = self._tool_registry.register_tool(WebFetchTool())
                code_id = self._tool_registry.register_tool(CodeUtilsTool())
                self._tool_registry.assign_tools_to_agent(
                    agent_id, [fs_id, term_id, web_id, code_id]
                )
        except Exception as e:  # noqa: BLE001
            # Best-effort only in MVP
            logger.error(f"Error registering tools for agent {agent_id}: {e}")
            pass
        # Update monitoring (status only). The monitor service emits agent.registered on ready.
        try:
            mon = get_monitoring()
            mon.set_agent_status(
                str(agent_id), agent_name, status="ready", config=config_data
            )
            # Emit event so UIs refresh active agents
            await mon.record_event(
                "agent.registered", {"agent_id": str(agent_id), "name": agent_name}
            )
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
            await mon.record_event("agent.unregistered", {"agent_id": str(agent_id)})
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
        conversation_id: ConversationID | None = None,
        session_id: str | None = None,
    ) -> AgentResponse:
        agent: IAgent | None = None
        if target is not None:
            agent = self._id_to_agent.get(target)
        else:
            agent = next(iter(self._id_to_agent.values()), None)
        if agent is None:
            raise RuntimeError("No registered agents to route message to")
        # Minimal context
        from l6e_forge.types.core import AgentContext  # local import to avoid cycles

        ctx = AgentContext(
            conversation_id=conversation_id or uuid.uuid4(),
            session_id=session_id or "local",
        )
        # Request logging moved to API layer to avoid duplicates
        # Best-effort: store conversation message in memory and attach history/provider to context
        try:
            mm = self.get_memory_manager()
            await mm.store_conversation(ctx.conversation_id, message)
            # Attach conversation history and provider for agent use
            from l6e_forge.memory.conversation.provider import (
                ConversationHistoryProvider,
            )

            try:
                ctx.conversation_history = await mm.get_conversation(
                    ctx.conversation_id, limit=50
                )
            except Exception:
                ctx.conversation_history = []
            ctx.history_provider = ConversationHistoryProvider(mm)
        except Exception:
            pass
        import time as _time

        _start = _time.perf_counter()
        resp = await agent.handle_message(message, ctx)
        # Process result with configurable processor (agent override or env default)
        try:
            # Agent-provided processor instance or default no-op
            processor_inst = None
            get_rp_inst = getattr(agent, "get_result_processor", None)
            if callable(get_rp_inst):  # type: ignore[call-arg]
                processor_inst = get_rp_inst()  # type: ignore[call-arg]
            if processor_inst is None:
                from l6e_forge.runtime.result_processing import get_default_processor

                processor_inst = get_default_processor()
            resp = await processor_inst.process(resp, context=ctx)  # type: ignore[arg-type]
        except Exception:
            pass
        # Ensure response object integrity for UI
        try:
            if not getattr(resp, "agent_id", None):
                resp.agent_id = self._id_to_name.get(
                    target or next(iter(self._id_to_name.keys()), uuid.uuid4()),
                    "unknown",
                )  # type: ignore[attr-defined]
            if not getattr(resp, "content", None):
                resp.content = ""  # type: ignore[attr-defined]
        except Exception:
            pass
        _elapsed_ms = (_time.perf_counter() - _start) * 1000.0
        # Record performance metric only; chat/event logging handled at API layer
        try:
            mon = get_monitoring()
            await mon.record_metric(
                "response_time_ms", _elapsed_ms, tags={"agent": resp.agent_id}
            )
        except Exception:
            pass
        return resp

    async def broadcast_message(
        self, message: Message, filter_fn: Callable | None = None
    ) -> list[AgentResponse]:
        results: list[AgentResponse] = []
        for agent in self._id_to_agent.values():
            if filter_fn and not filter_fn(agent):  # type: ignore[arg-type]
                continue
            from l6e_forge.types.core import (
                AgentContext,
            )  # local import to avoid cycles

            ctx = AgentContext(conversation_id=uuid.uuid4(), session_id="local")
            results.append(await agent.handle_message(message, ctx))
        return results

    # Resource management (stubs)
    def get_memory_manager(self):  # -> IMemoryManager
        if self._memory_manager is None:
            # Default to in-memory vector store and provider-backed embedding if available
            from l6e_forge.memory.backends.inmemory import InMemoryVectorStore
            from l6e_forge.memory.backends.qdrant import QdrantVectorStore
            from l6e_forge.memory.managers.memory import MemoryManager
            from l6e_forge.memory.embeddings.ollama import OllamaEmbeddingProvider
            from l6e_forge.memory.embeddings.lmstudio import LMStudioEmbeddingProvider
            from l6e_forge.memory.embeddings.mock import MockEmbeddingProvider

            # Choose store based on env/config; default to in-memory
            store = InMemoryVectorStore()
            try:
                # If QDRANT_URL or AF_MEMORY_PROVIDER=qdrant, use Qdrant
                if (
                    os.environ.get("QDRANT_URL")
                    or os.environ.get("AF_MEMORY_PROVIDER") == "qdrant"
                ):
                    store = QdrantVectorStore()
            except Exception:
                pass
            # Prefer Ollama embeddings if reachable, else LM Studio, else mock
            embedder = None
            try:
                import httpx

                # Probe Ollama
                ollama = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip(
                    "/"
                )
                r = httpx.get(f"{ollama}/api/version", timeout=1.0)
                if r.status_code == 200:
                    embedder = OllamaEmbeddingProvider()
            except Exception:
                embedder = None
            if embedder is None:
                try:
                    import httpx

                    lm = os.environ.get(
                        "LMSTUDIO_HOST", "http://localhost:1234/v1"
                    ).rstrip("/")
                    r = httpx.get(f"{lm}/models", timeout=1.0)
                    if r.status_code == 200:
                        embedder = LMStudioEmbeddingProvider()
                except Exception:
                    embedder = None
            if embedder is None:
                embedder = MockEmbeddingProvider()
            # Optional conversation store (Postgres) if AF_DB_URL is set
            conversation_store = None
            try:
                db_url = os.environ.get("AF_DB_URL", "").strip()
                if db_url:
                    from l6e_forge.memory.conversation.postgres import (
                        PostgresConversationStore,
                    )

                    conversation_store = PostgresConversationStore(db_url)
            except Exception:
                conversation_store = None
            self._memory_manager = MemoryManager(store, embedder, conversation_store)
        return self._memory_manager

    def get_model_manager(self):  # -> IModelManager
        if self._model_manager is None:
            # Use provider registry with endpoints from forge.toml (workspace root is parent of agents dir)
            from l6e_forge.models.providers.registry import (
                load_endpoints_from_config,
                get_manager,
            )

            workspace_root = Path.cwd()
            _default_provider, endpoints = load_endpoints_from_config(workspace_root)
            provider = (
                os.environ.get("AF_DEFAULT_PROVIDER") or _default_provider or "ollama"
            )
            self._model_manager = get_manager(provider, endpoints)
        return self._model_manager

    def get_tool_registry(self):  # -> IToolRegistry
        if self._tool_registry is None:
            from l6e_forge.tools.registry.inmemory import InMemoryToolRegistry

            self._tool_registry = InMemoryToolRegistry()
        return self._tool_registry

    def get_event_bus(self):  # -> IEventBus
        raise NotImplementedError

    # Development support (stubs)
    async def start_dev_mode(self, port: int = 8123) -> None:
        return None

    async def enable_hot_reload(self, watch_paths: list[Path]) -> None:
        return None

    # Convenience: registered agent views
    def list_registered(self) -> list[dict[str, str]]:
        items: list[dict[str, str]] = []
        for aid, name in self._id_to_name.items():
            items.append({"agent_id": str(aid), "name": name})
        return items

    def get_agent_id_by_name(self, name: str) -> AgentID | None:
        return self._name_to_id.get(name)
