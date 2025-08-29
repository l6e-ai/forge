from __future__ import annotations

import os
import asyncio
from pathlib import Path
import sys
import json
import time

import typer
from rich import print as rprint
from rich.console import Console
from rich.markdown import Markdown

from l6e_forge.models.managers.base import IModelManager
from l6e_forge.types.core import Message, AgentContext
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from l6e_forge.runtime.local import LocalRuntime
from l6e_forge.config_managers.toml import TomlConfigManager
from l6e_forge.models.managers.ollama import OllamaModelManager
from l6e_forge.models.managers.lmstudio import LMStudioModelManager
from l6e_forge.types.model import ModelSpec
from l6e_forge.runtime.monitoring import get_monitoring
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


async def _stream_ollama_chat(
    endpoint: str, model: str, messages: list[Message]
) -> None:
    url = f"{endpoint.rstrip('/')}/api/chat"
    payload = {
        "model": model,
        "messages": [{"role": m.role, "content": m.content} for m in messages],
        "stream": True,
    }
    try:
        import httpx  # local import to avoid hard dep in non-stream paths

        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", url, json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        content = data.get("message", {}).get("content") or data.get(
                            "delta"
                        )
                        if content:
                            sys.stdout.write(str(content))
                            sys.stdout.flush()
                    except Exception:
                        # Write raw if malformed
                        sys.stdout.write(line)
                        sys.stdout.flush()
        sys.stdout.write("\n")
        sys.stdout.flush()
    except Exception as exc:  # noqa: BLE001
        rprint(f"[red]Error (Ollama stream):[/red] {exc}")
        raise


async def _stream_lmstudio_chat(
    endpoint: str, model: str, messages: list[Message]
) -> None:
    url = f"{endpoint.rstrip('/')}/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": m.role, "content": m.content} for m in messages],
        "stream": True,
    }
    try:
        import httpx  # local import to avoid hard dep in non-stream paths

        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", url, json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("data: "):
                        line = line[len("data: ") :]
                    if line.strip() == "[DONE]":
                        break
                    try:
                        data = json.loads(line)
                        delta = (
                            (data.get("choices") or [{}])[0].get("delta") or {}
                        ).get("content") or (
                            (data.get("choices") or [{}])[0].get("message") or {}
                        ).get("content")
                        if delta:
                            sys.stdout.write(str(delta))
                            sys.stdout.flush()
                    except Exception:
                        sys.stdout.write(line)
                        sys.stdout.flush()
        sys.stdout.write("\n")
        sys.stdout.flush()
    except Exception as exc:  # noqa: BLE001
        rprint(f"[red]Error (LM Studio stream):[/red] {exc}")
        raise


@app.command()
def chat(
    agent: str = typer.Argument(..., help="Agent name"),
    message: str = typer.Option(
        "", "--message", "-m", help="Send a single message and exit"
    ),
    workspace: str | None = typer.Option(
        None, "--workspace", "-w", help="Workspace root path"
    ),
    stream: bool = typer.Option(
        True, "--stream/--no-stream", help="Stream responses when using providers"
    ),
    monitor_url: str | None = typer.Option(
        None, "--monitor-url", help="Monitoring base URL (overrides env/config)"
    ),
    markdown: bool = typer.Option(
        True,
        "--markdown/--no-markdown",
        help="Render responses as Markdown in the terminal",
    ),
    debug: bool = typer.Option(
        False, "--debug", help="Print full tracebacks on errors"
    ),
    timeout: float = typer.Option(
        90.0, "--timeout", help="Model request timeout in seconds (direct providers)"
    ),
):
    """Send a message to an agent and print the response."""
    root = _resolve_workspace(workspace)
    console = Console()

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
            if (
                isinstance(cfg_monitor_url, str)
                and not os.environ.get("AF_MONITOR_URL")
                and monitor_url is None
            ):
                os.environ["AF_MONITOR_URL"] = cfg_monitor_url
    except Exception:
        pass

    # Environment overrides for endpoints (useful in Docker: host.docker.internal)
    env_ollama = os.environ.get("OLLAMA_HOST")
    env_lmstudio = os.environ.get("LMSTUDIO_HOST")
    if env_ollama:
        endpoints["ollama"] = env_ollama
    if env_lmstudio:
        endpoints["lmstudio"] = env_lmstudio

    # Ensure monitoring is configured for this process if not already
    if not os.environ.get("AF_MONITOR_URL"):
        use_url = (
            monitor_url or os.environ.get("AF_MONITOR_URL") or "http://localhost:8321"
        )
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

    def _print_response(text: str) -> None:
        # Normalize and ensure string
        try:
            s = "" if text is None else str(text)
        except Exception:
            s = ""  # last resort
        # Replace CR with LF and ensure terminal-friendly newlines
        s = s.replace("\r\n", "\n").replace("\r", "\n")
        # Strip non-printable control chars except tab/newline
        s = "".join(ch for ch in s if ch == "\n" or ch == "\t" or ord(ch) >= 32)
        if markdown:
            try:
                console.print(Markdown(s), soft_wrap=True)
                return
            except Exception:
                # Fall back to plain text if markdown rendering isn't available
                pass
        try:
            rprint(s)
        except Exception:
            # Very defensive: raw write to stdout
            try:
                sys.stdout.write(s + "\n")
                sys.stdout.flush()
            except Exception:
                # Last-ditch attempt: encode ignoring errors
                try:
                    sys.stdout.buffer.write((s + "\n").encode("utf-8", errors="ignore"))
                    sys.stdout.flush()
                except Exception:
                    pass

    # One session per invocation
    session_uuid = str(uuid.uuid4())

    async def _run_once() -> int:
        # Minimal context
        msg = Message(content=message, role="user")
        conversation_id = uuid.uuid4()
        ctx = AgentContext(
            conversation_id=conversation_id,
            session_id=session_uuid,
            workspace_path=root,
        )
        try:
            if use_direct_model:
                if stream:
                    if use_provider == "ollama":
                        endpoint = endpoints.get(
                            "ollama",
                            os.environ.get("OLLAMA_HOST", "http://localhost:11434"),
                        )
                        await _stream_ollama_chat(endpoint, str(use_model), [msg])  # type: ignore[arg-type]
                    else:
                        endpoint = endpoints.get(
                            "lmstudio",
                            os.environ.get("LMSTUDIO_HOST", "http://localhost:1234/v1"),
                        )
                        await _stream_lmstudio_chat(endpoint, str(use_model), [msg])  # type: ignore[arg-type]
                else:
                    manager: IModelManager | None = None
                    if use_provider == "ollama":
                        endpoint = endpoints.get(
                            "ollama",
                            os.environ.get("OLLAMA_HOST", "http://localhost:11434"),
                        )
                        rprint(f"[cyan]Using provider:[/cyan] ollama at {endpoint}")
                        manager = OllamaModelManager(endpoint=endpoint)
                    else:
                        endpoint = endpoints.get(
                            "lmstudio",
                            os.environ.get("LMSTUDIO_HOST", "http://localhost:1234/v1"),
                        )
                        rprint(f"[cyan]Using provider:[/cyan] lmstudio at {endpoint}")
                        manager = LMStudioModelManager(endpoint=endpoint)
                    if not use_model:
                        raise ValueError("Model not set")
                    spec = ModelSpec(
                        model_id=use_model,
                        provider=use_provider,
                        model_name=use_model,
                        memory_requirement_gb=0.0,
                    )  # type: ignore[arg-type]
                    model_id = await manager.load_model(spec)
                    # Monitoring for direct-model path
                    mon = get_monitoring()
                    d_agent_id, d_name = _direct_identifiers()
                    # Mark agent as ready so UI shows it
                    mon.set_agent_status(
                        d_agent_id,
                        d_name,
                        status="ready",
                        config={"provider": use_provider, "model": use_model},
                    )
                    mon.add_chat_log(
                        conversation_id=str(ctx.conversation_id),
                        role=msg.role,
                        content=msg.content,
                    )
                    await mon.record_event(
                        "chat.message", {"direction": "in", "role": msg.role}
                    )
                    _start = time.perf_counter()
                    resp = await manager.chat(model_id, [msg], timeout=timeout)
                    elapsed_ms = (time.perf_counter() - _start) * 1000.0
                    _print_response(resp.message.content)
                    mon.add_chat_log(
                        conversation_id=str(ctx.conversation_id),
                        role="assistant",
                        content=resp.message.content,
                        agent_id=d_agent_id,
                    )
                    await mon.record_metric(
                        "response_time_ms", elapsed_ms, tags={"agent": d_agent_id}
                    )
                    await mon.record_event(
                        "chat.message", {"direction": "out", "agent": d_agent_id}
                    )
            else:
                assert runtime is not None and agent_id is not None
                resp = await runtime.route_message(
                    msg,
                    target=agent_id,
                    conversation_id=conversation_id,
                    session_id=session_uuid,
                )
                _print_response(resp.content)
        except Exception as exc:  # noqa: BLE001
            import traceback

            err_type = type(exc).__name__
            err_msg = str(exc) or repr(exc)
            rprint(f"[red]Error ({err_type}):[/red] {err_msg}")
            if debug:
                rprint(traceback.format_exc())
            return 1
        return 0

    def _cleanup() -> None:
        try:
            if use_direct_model:
                mon = get_monitoring()
                d_agent_id, _ = _direct_identifiers()
                # Best-effort removal
                mon.remove_agent(d_agent_id)
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

        prompt_session: PromptSession = PromptSession(
            message=f"{agent}> ",
            history=FileHistory(str(history_file)),
            auto_suggest=AutoSuggestFromHistory(),
        )

        rprint(
            "[green]Interactive chat. Press Ctrl+D to exit, Ctrl+C to clear line.[/green]"
        )
        conversation: list[Message] = []
        # Track rapid Ctrl+C presses to provide an exit hint on double press
        last_interrupt_time = 0.0
        interrupt_count = 0
        # Seed conversation in streaming direct-model mode to avoid empty-history errors
        if use_direct_model and stream:
            conversation.append(
                Message(content="You are a helpful assistant.", role="system")
            )
        while True:
            try:
                user_input = prompt_session.prompt()
                # Successful input resets the interrupt counter
                interrupt_count = 0
            except KeyboardInterrupt:
                # Clear the current line; on rapid double Ctrl+C, gently hint about Ctrl+D
                now = time.monotonic()
                if now - last_interrupt_time < 1.5:
                    interrupt_count += 1
                else:
                    interrupt_count = 1
                last_interrupt_time = now
                if interrupt_count >= 2:
                    rprint("[yellow]Tip:[/yellow] Press Ctrl+D to exit the chat.")
                continue
            except EOFError:
                rprint("\n[yellow]Exiting chat.[/yellow]")
                _cleanup()
                raise typer.Exit(code=0)

            if not user_input.strip():
                continue

            async def _run_one_msg(text: str) -> int:
                msg = Message(content=text, role="user")
                conversation_id = uuid.uuid4()
                try:
                    if use_direct_model:
                        conversation.append(msg)
                        if stream:
                            if use_provider == "ollama":
                                endpoint = endpoints.get(
                                    "ollama",
                                    os.environ.get(
                                        "OLLAMA_HOST", "http://localhost:11434"
                                    ),
                                )
                                await _stream_ollama_chat(
                                    endpoint, str(use_model), conversation
                                )  # type: ignore[arg-type]
                            else:
                                endpoint = endpoints.get(
                                    "lmstudio",
                                    os.environ.get(
                                        "LMSTUDIO_HOST", "http://localhost:1234/v1"
                                    ),
                                )
                                await _stream_lmstudio_chat(
                                    endpoint, str(use_model), conversation
                                )  # type: ignore[arg-type]
                        else:
                            manager: IModelManager | None = None
                            if use_provider == "ollama":
                                endpoint = endpoints.get(
                                    "ollama",
                                    os.environ.get(
                                        "OLLAMA_HOST", "http://localhost:11434"
                                    ),
                                )
                                rprint(
                                    f"[cyan]Using provider:[/cyan] ollama at {endpoint}"
                                )
                                manager = OllamaModelManager(endpoint=endpoint)
                            else:
                                endpoint = endpoints.get(
                                    "lmstudio",
                                    os.environ.get(
                                        "LMSTUDIO_HOST", "http://localhost:1234/v1"
                                    ),
                                )
                                rprint(
                                    f"[cyan]Using provider:[/cyan] lmstudio at {endpoint}"
                                )
                                manager = LMStudioModelManager(endpoint=endpoint)
                            if not use_model:
                                raise ValueError("Model not set")
                            spec = ModelSpec(
                                model_id=use_model,
                                provider=use_provider,
                                model_name=use_model,
                                memory_requirement_gb=0.0,
                            )  # type: ignore[arg-type]
                            model_id = await manager.load_model(spec)
                            resp = await manager.chat(
                                model_id,
                                conversation,
                                timeout=timeout,
                            )  # type: ignore[arg-type]
                            _print_response(resp.message.content)
                            conversation.append(resp.message)
                    else:
                        assert runtime is not None and agent_id is not None
                        resp = await runtime.route_message(
                            msg,
                            target=agent_id,
                            conversation_id=conversation_id,
                            session_id=session_uuid,
                        )
                        _print_response(resp.content)
                except Exception as exc:  # noqa: BLE001
                    import traceback

                    err_type = type(exc).__name__
                    err_msg = str(exc) or repr(exc)
                    rprint(f"[red]Error ({err_type}):[/red] {err_msg}")
                    if debug:
                        rprint(traceback.format_exc())
                    return 1
                return 0

            code = asyncio.run(_run_one_msg(user_input))
            if code != 0:
                if debug:
                    rprint(
                        "[yellow]Continuing after error. Type another message or Ctrl+D to exit.[/yellow]"
                    )
                continue
        # Unreachable

    code = asyncio.run(_run_once())
    _cleanup()
    raise typer.Exit(code=code)


def main() -> None:
    app()
