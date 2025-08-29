from __future__ import annotations

from pathlib import Path
import sys
import os
import subprocess

import typer
from rich import print as rprint
from rich.table import Table

from l6e_forge.workspace.manager.local import LocalWorkspaceManager
from l6e_forge_cli import create as create_cmd
from l6e_forge_cli import dev as dev_cmd
from l6e_forge_cli.chat import chat as chat_command
from l6e_forge_cli import template as template_cmd
from l6e_forge_cli import models as models_cmd
from l6e_forge.dev.service import DevService
from l6e_forge_cli import package as package_cmd
from l6e_forge_cli import memory as memory_cmd

app = typer.Typer(help="l6e-forge CLI")
app.add_typer(create_cmd.app, name="create")
app.add_typer(dev_cmd.app, name="dev")
# Register chat as a top-level command (invoke as `forge chat ...`)
app.command(name="chat")(chat_command)
app.add_typer(template_cmd.app, name="template")
app.add_typer(models_cmd.app, name="models")
app.add_typer(package_cmd.app, name="pkg")
app.add_typer(memory_cmd.app, name="memory")


@app.command()
def init(
    workspace: str = typer.Argument(..., help="Path to create the workspace in"),
    with_example: bool = typer.Option(
        False, "--with-example", help="Also scaffold a sample agent 'demo'"
    ),
    with_compose: bool = typer.Option(
        True,
        "--with-compose/--no-with-compose",
        help="Include a production docker-compose.yml in the workspace",
    ),
    conversation_store: str = typer.Option(
        "postgres",
        "--conversation-store",
        help="Conversation store to configure (postgres|none)",
    ),
):
    """Create a new l6e-forge workspace at the given path."""
    manager = LocalWorkspaceManager()
    path = Path(workspace)
    try:
        typer.echo(f"Creating workspace at: {path}")
        import asyncio

        asyncio.run(
            manager.create_workspace(
                path, with_compose=with_compose, conversation_store=conversation_store
            )
        )
        # Ensure new default directories exist (robustness if manager changes)
        try:
            (path / "templates").mkdir(parents=True, exist_ok=True)
            (path / "prompts").mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        # Optionally scaffold an example agent to get started quickly
        if with_example:
            try:
                from l6e_forge_cli.create import agent as create_agent

                create_agent.callback  # type: ignore[attr-defined]
                # run the command function directly
                create_agent(
                    name="demo",
                    workspace=str(path),
                    provider="ollama",
                    model="llama3.2:3b",
                    provider_endpoint=None,
                    template="assistant",
                )
            except Exception:
                rprint(
                    "[yellow]Failed to scaffold example agent. You can create one later with 'forge create <name>'.[/yellow]"
                )
        rprint("[green]Workspace created successfully.[/green]")
    except Exception as exc:  # noqa: BLE001
        rprint(f"[red]Failed to create workspace:[/red] {exc}")
        raise typer.Exit(code=1)


@app.command(name="list")
def list_command() -> None:  # noqa: A003 - intentional CLI verb
    """List agents in the current workspace."""
    manager = LocalWorkspaceManager()
    import asyncio

    state = asyncio.run(manager.load_workspace(Path.cwd()))

    table = Table(title="Agents")
    table.add_column("Name")
    if state.agent_count == 0:
        rprint(
            "[yellow]No agents found. Create one with 'forge create <name>'.[/yellow]"
        )
        return
    for name in state.active_agents:
        table.add_row(name)
    rprint(table)


def _find_compose_file(provided: str | None) -> Path | None:
    if provided:
        p = Path(provided).expanduser().resolve()
        return p if p.exists() else None
    env_p = os.environ.get("AF_COMPOSE_FILE")
    if env_p:
        p = Path(env_p).expanduser().resolve()
        if p.exists():
            return p
    # Try package root (dev repo scenario)
    try:
        pkg_root = Path(__file__).resolve().parents[2]
        candidate = pkg_root / "docker-compose.yml"
        if candidate.exists():
            return candidate
    except Exception:
        pass
    # Try walking up from cwd
    start = Path.cwd()
    for d in [start] + list(start.parents):
        for name in (
            "docker-compose.yml",
            "docker-compose.yaml",
            "compose.yml",
            "compose.yaml",
        ):
            c = d / name
            if c.exists():
                return c
    return None


def _run_compose(compose_file: Path, args: list[str]) -> int:
    base = ["docker", "compose", "-f", str(compose_file)]
    try:
        proc = subprocess.run(base + args, check=False)
        return proc.returncode
    except FileNotFoundError:
        # Fallback to docker-compose if classic plugin not available
        base = ["docker-compose", "-f", str(compose_file)]
        proc = subprocess.run(base + args, check=False)
        return proc.returncode


@app.command()
def up(
    workspace: str | None = typer.Option(
        None, "--workspace", "-w", help="Workspace root path"
    ),
    compose_file: str | None = typer.Option(
        None, "--compose-file", "-f", help="Path to docker compose file"
    ),
    monitor_url: str = typer.Option(
        "http://localhost:8321", "--monitor-url", help="Monitor base URL"
    ),
    no_dev: bool = typer.Option(False, "--no-dev", help="Do not start dev runtime"),
    dev_only: bool = typer.Option(
        False, "--dev-only", help="Only start dev runtime; skip containers"
    ),
    build: bool = typer.Option(
        False, "--build", help="Build images before starting containers"
    ),
    open_ui: bool = typer.Option(
        True, "--open-ui/--no-open-ui", help="Open the UI in your browser after start"
    ),
) -> None:
    """Start local stack: containers (monitor) and dev runtime with monitoring wired."""
    compose_path = _find_compose_file(compose_file)
    if not dev_only:
        if compose_path is None:
            rprint(
                "[red]Compose file not found. Provide --compose-file or set AF_COMPOSE_FILE.[/red]"
            )
            raise typer.Exit(code=1)
        rprint(f"[cyan]Using compose file:[/cyan] {compose_path}")
        args = ["up", "-d"]
        if build:
            args.append("--build")
        code = _run_compose(compose_path, args)
        if code != 0:
            raise typer.Exit(code=code)
        rprint("[green]Containers started.[/green]")
        if open_ui:
            try:
                import webbrowser

                webbrowser.open("http://localhost:8173", new=2)
            except Exception:
                pass

    if not no_dev:
        # Resolve workspace and start dev mode with AF_MONITOR_URL set
        path_str = workspace or os.environ.get("PWD") or str(Path.cwd())
        root = Path(path_str).expanduser().resolve()
        is_workspace = (root / "forge.toml").exists() and (root / "agents").exists()
        if not is_workspace:
            rprint(f"[red]Not a workspace: {root}[/red]")
            raise typer.Exit(code=1)
        os.environ["AF_MONITOR_URL"] = monitor_url
        rprint(f"[cyan]AF_MONITOR_URL=[/cyan] {monitor_url}")
        os.environ["AF_UI_URL"] = "http://localhost:8173"
        rprint(f"[cyan]AF_UI_URL=[/cyan] {os.environ['AF_UI_URL']}")
        service = DevService(root)
        code = service.start()
        raise typer.Exit(code=code)
    else:
        # If only containers were started, exit 0
        raise typer.Exit(code=0)


@app.command()
def down(
    compose_file: str | None = typer.Option(
        None, "--compose-file", "-f", help="Path to docker compose file"
    ),
    volumes: bool = typer.Option(False, "--volumes", "-v", help="Remove named volumes"),
) -> None:
    """Stop local container stack (monitor, etc)."""
    compose_path = _find_compose_file(compose_file)
    if compose_path is None:
        rprint(
            "[red]Compose file not found. Provide --compose-file or set AF_COMPOSE_FILE.[/red]"
        )
        raise typer.Exit(code=1)
    rprint(f"[cyan]Using compose file:[/cyan] {compose_path}")
    args = ["down"]
    if volumes:
        args.append("--volumes")
    code = _run_compose(compose_path, args)
    raise typer.Exit(code=code)


def main() -> int:
    return app()


if __name__ == "__main__":
    sys.exit(main())
