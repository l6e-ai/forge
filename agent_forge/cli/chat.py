from __future__ import annotations

import os
import asyncio
from pathlib import Path
import time

import typer
from rich import print as rprint

from agent_forge.types.core import Message, AgentContext
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from agent_forge.runtime.local import LocalRuntime
from agent_forge.config_managers.toml import TomlConfigManager
from agent_forge.models.providers.registry import get_manager
from agent_forge.types.model import ModelSpec
from agent_forge.runtime.monitoring import get_monitoring
import uuid


app = typer.Typer(help="Chat with an agent in the current workspace")


def _resolve_workspace(workspace: str | None) -> Path:
    path_str = workspace or os.environ.get("PWD") or str(Path.cwd())
    return Path(path_str).expanduser().resolve()


async def _prepare_runtime(workspace_root: Path, agent_name: str):
    agent_dir = workspace_root / "agents" / agent_name
    if not (agent_dir / "agent.py").exists():
        raise FileNotFoundError(f"Agent not found: {agent_name} at {agent_dir}")
    runtime = LocalRuntime()
    agent_id = await runtime.register_agent(agent_dir)
    return runtime, agent_id


@app.command()
def chat(
    agent: str = typer.Argument(..., help="Agent name"),
    message: str = typer.Option("", "--message", "-m", help="Send a single message and exit"),
    workspace: str | None = typer.Option(None, "--workspace", "-w", help="Workspace root path"),
    monitor_url: str | None = typer.Option(None, "--monitor-url", help="Monitoring base URL (overrides env/config)"),
):
    """Send a message to an agent and print the response."""
    root = _resolve_workspace(workspace)
    # Load config defaults (agent-level first, then workspace-level)
    provider_from_cfg: str | None = None
    model_from_cfg: str | None = None
    endpoints: dict[str, str] = {}
    try:
        cfg_mgr = TomlConfigManager()
        agent_cfg_path = root / "agents" / agent / "config.toml"
        if agent_cfg_path.exists():
            _ = asyncio.run(cfg_mgr.load_config(agent_cfg_path))
            provider_from_cfg = cfg_mgr.get_config_value("agent.provider")
            model_from_cfg = cfg_mgr.get_config_value("agent.model")
        # workspace defaults
        ws_cfg_path = root / "forge.toml"
        if ws_cfg_path.exists():
            _ = asyncio.run(cfg_mgr.load_config(ws_cfg_path))
            if provider_from_cfg is None:
                provider_from_cfg = cfg_mgr.get_config_value("models.default_provider")
            if model_from_cfg is None:
                model_from_cfg = cfg_mgr.get_config_value("models.default_model")
            ep_ollama = cfg_mgr.get_config_value("models.endpoints.ollama")
            ep_lmstudio = cfg_mgr.get_config_value("models.endpoints.lmstudio")
            if isinstance(ep_ollama, str):
                endpoints["ollama"] = ep_ollama
            if isinstance(ep_lmstudio, str):
                endpoints["lmstudio"] = ep_lmstudio
            # optional monitor url in config
            cfg_monitor_url = cfg_mgr.get_config_value("monitor.url")
            if isinstance(cfg_monitor_url, str) and not os.environ.get("AF_MONITOR_URL") and monitor_url is None:
                os.environ["AF_MONITOR_URL"] = cfg_monitor_url
    except Exception:
        pass

    # Ensure monitoring is configured for this process if not already
    if not os.environ.get("AF_MONITOR_URL"):
        use_url = monitor_url or os.environ.get("AF_MONITOR_URL") or "http://localhost:8321"
        os.environ["AF_MONITOR_URL"] = use_url

    use_provider = (provider_from_cfg or "").lower()
    use_model = model_from_cfg

    use_direct_model = use_provider in ("ollama", "lmstudio") and bool(use_model)

    runtime = None
    agent_id = None
    if not use_direct_model:
        try:
            runtime, agent_id = asyncio.run(_prepare_runtime(root, agent))
        except Exception as exc:  # noqa: BLE001
            rprint(f"[red]{exc}[/red]")
            raise typer.Exit(code=1)

    def _direct_identifiers() -> tuple[str, str]:
        ident = f"direct:{use_provider}:{use_model}"
        display = f"{agent} ({use_provider}:{use_model})"
        return ident, display

    # One session per invocation
    session_uuid = str(uuid.uuid4())

    async def _run_once() -> int:
        # Minimal context
        msg = Message(content=message, role="user")
        conversation_id = f"{agent}:{session_uuid}"
        ctx = AgentContext(conversation_id=conversation_id, session_id=session_uuid, workspace_path=root)
        try:
            if use_direct_model:
                manager = get_manager(use_provider, endpoints)
                spec = ModelSpec(model_id=use_model, provider=use_provider, model_name=use_model, memory_requirement_gb=0.0)  # type: ignore[arg-type]
                model_id = await manager.load_model(spec)
                # Monitoring for direct-model path
                mon = get_monitoring()
                d_agent_id, d_name = _direct_identifiers()
                # Mark agent as ready so UI shows it
                mon.set_agent_status(d_agent_id, d_name, status="ready", config={"provider": use_provider, "model": use_model})
                mon.add_chat_log(conversation_id=ctx.conversation_id or "local", role=msg.role, content=msg.content)
                await mon.record_event("chat.message", {"direction": "in", "role": msg.role})
                _start = time.perf_counter()
                resp = await manager.chat(model_id, [msg])
                elapsed_ms = (time.perf_counter() - _start) * 1000.0
                mon.add_chat_log(conversation_id=ctx.conversation_id or "local", role="assistant", content=resp.message.content, agent_id=d_agent_id)
                await mon.record_metric("response_time_ms", elapsed_ms, tags={"agent": d_agent_id})
                await mon.record_event("chat.message", {"direction": "out", "agent": d_agent_id})
                rprint(resp.message.content)
            else:
                assert runtime is not None and agent_id is not None
                resp = await runtime.route_message(msg, target=agent_id, conversation_id=conversation_id, session_id=session_uuid)
                rprint(resp.content)
        except Exception as exc:  # noqa: BLE001
            rprint(f"[red]Error:[/red] {exc}")
            return 1
        return 0

    def _cleanup() -> None:
        try:
            if use_direct_model:
                mon = get_monitoring()
                d_agent_id, _ = _direct_identifiers()
                # Best-effort removal
                mon.remove_agent(d_agent_id)  # type: ignore[attr-defined]
            else:
                assert runtime is not None and agent_id is not None
                try:
                    asyncio.run(runtime.unregister_agent(agent_id))
                except Exception:
                    pass
        except Exception:
            pass

    if not message:
        # Interactive mode
        history_dir = root / ".forge" / "logs"
        history_dir.mkdir(parents=True, exist_ok=True)
        history_file = history_dir / f"chat-history-{agent}.txt"

        session = PromptSession(
            message=f"{agent}> ",
            history=FileHistory(str(history_file)),
            auto_suggest=AutoSuggestFromHistory(),
        )

        rprint("[green]Interactive chat. Press Ctrl+D to exit, Ctrl+C to clear line.[/green]")
        conversation: list[Message] = []
        while True:
            try:
                user_input = session.prompt()
            except KeyboardInterrupt:
                # Clear the current line
                continue
            except EOFError:
                rprint("\n[yellow]Exiting chat.[/yellow]")
                _cleanup()
                raise typer.Exit(code=0)

            if not user_input.strip():
                continue

            async def _run_one_msg(text: str) -> int:
                msg = Message(content=text, role="user")
                conversation_id = f"{agent}:{session_uuid}"
                ctx = AgentContext(conversation_id=conversation_id, session_id=session_uuid, workspace_path=root)
                try:
                    if use_direct_model:
                        manager = get_manager(use_provider, endpoints)
                        conversation.append(msg)
                        # Monitoring for direct-model path
                        mon = get_monitoring()
                        d_agent_id, d_name = _direct_identifiers()
                        mon.set_agent_status(d_agent_id, d_name, status="ready", config={"provider": use_provider, "model": use_model})
                        mon.add_chat_log(conversation_id=ctx.conversation_id or "local", role=msg.role, content=msg.content)
                        await mon.record_event("chat.message", {"direction": "in", "role": msg.role})
                        _start = time.perf_counter()
                        resp = await manager.chat(await manager.load_model(ModelSpec(model_id=use_model, provider=use_provider, model_name=use_model, memory_requirement_gb=0.0)), conversation)  # type: ignore[arg-type]
                        elapsed_ms = (time.perf_counter() - _start) * 1000.0
                        rprint(resp.message.content)
                        conversation.append(resp.message)
                        mon.add_chat_log(conversation_id=ctx.conversation_id or "local", role="assistant", content=resp.message.content, agent_id=d_agent_id)
                        await mon.record_metric("response_time_ms", elapsed_ms, tags={"agent": d_agent_id})
                        await mon.record_event("chat.message", {"direction": "out", "agent": d_agent_id})
                    else:
                        assert runtime is not None and agent_id is not None
                        resp = await runtime.route_message(msg, target=agent_id, conversation_id=conversation_id, session_id=session_uuid)
                        rprint(resp.content)
                except Exception as exc:  # noqa: BLE001
                    rprint(f"[red]Error:[/red] {exc}")
                    return 1
                return 0

            code = asyncio.run(_run_one_msg(user_input))
            if code != 0:
                _cleanup()
                raise typer.Exit(code=code)
        # Unreachable

    code = asyncio.run(_run_once())
    _cleanup()
    raise typer.Exit(code=code)


def main() -> None:
    app()


