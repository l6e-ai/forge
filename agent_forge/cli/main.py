from __future__ import annotations

from pathlib import Path
import sys

import typer
from rich import print as rprint
from rich.table import Table

from agent_forge.workspace.manager.local import LocalWorkspaceManager
from agent_forge.cli import create as create_cmd
from agent_forge.cli import dev as dev_cmd
from agent_forge.cli import chat as chat_cmd
from agent_forge.cli import template as template_cmd
from agent_forge.cli import models as models_cmd

app = typer.Typer(help="Agent-Forge CLI")
app.add_typer(create_cmd.app, name="create")
app.add_typer(dev_cmd.app, name="dev")
app.add_typer(chat_cmd.app, name="chat")
app.add_typer(template_cmd.app, name="template")
app.add_typer(models_cmd.app, name="models")


@app.command()
def init(
    workspace: str = typer.Argument(..., help="Path to create the workspace in"),
):
    """Create a new Agent-Forge workspace at the given path."""
    manager = LocalWorkspaceManager()
    path = Path(workspace)
    try:
        typer.echo(f"Creating workspace at: {path}")
        import asyncio

        asyncio.run(manager.create_workspace(path))
        rprint("[green]Workspace created successfully.[/green]")
    except Exception as exc:  # noqa: BLE001
        rprint(f"[red]Failed to create workspace:[/red] {exc}")
        raise typer.Exit(code=1)


@app.command()
def list() -> None:  # noqa: A003 - intentional CLI verb
    """List agents in the current workspace."""
    manager = LocalWorkspaceManager()
    import asyncio

    state = asyncio.run(manager.load_workspace(Path.cwd()))

    table = Table(title="Agents")
    table.add_column("Name")
    if state.agent_count == 0:
        rprint("[yellow]No agents found. Create one with 'forge create <name>'.[/yellow]")
        return
    for name in state.active_agents:
        table.add_row(name)
    rprint(table)


def main() -> None:
    app()


if __name__ == "__main__":
    sys.exit(main())


