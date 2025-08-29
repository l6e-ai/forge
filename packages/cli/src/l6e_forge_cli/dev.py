from __future__ import annotations

import os
import asyncio
from pathlib import Path

import typer
from rich import print as rprint

from l6e_forge.workspace.manager.local import LocalWorkspaceManager
from l6e_forge.dev.service import DevService


app = typer.Typer(help="Development server and hot reload")


@app.callback(invoke_without_command=True)
def dev(
    workspace: str | None = typer.Option(
        None, "--workspace", "-w", help="Workspace root path"
    ),
    check: bool = typer.Option(False, "--check", help="Validate workspace and exit"),
    run_for: float | None = typer.Option(
        None, "--run-for", help="Run dev mode for N seconds then exit (testing)"
    ),
    test_touch: list[str] = typer.Option(
        None,
        "--test-touch",
        help="[TEST] Touch paths after start to trigger reload",
        hidden=True,
    ),
) -> None:
    """Start dev mode (hot reload) or just validate with --check."""
    manager = LocalWorkspaceManager()

    path_str = workspace or os.environ.get("PWD") or str(Path.cwd())
    root = Path(path_str).expanduser().resolve()

    is_workspace = (root / "forge.toml").exists() and (root / "agents").exists()

    if check:
        if not is_workspace:
            rprint(f"[red]Not a workspace: {root}[/red]")
            raise typer.Exit(code=1)
        result = asyncio.run(manager.validate_workspace(root))
        if not result.is_valid:
            rprint(f"[red]Workspace validation failed for {root}[/red]")
            for err in result.errors:
                rprint(f" - {err}")
            raise typer.Exit(code=1)
        rprint("[green]Dev mode ready: workspace validated.[/green]")
        raise typer.Exit(code=0)

    if not is_workspace:
        rprint(f"[red]Not a workspace: {root}[/red]")
        raise typer.Exit(code=1)

    service = DevService(root)
    code = service.start(run_for=run_for, test_touch=test_touch)
    raise typer.Exit(code=code)
