from __future__ import annotations

import typer

from agent_forge.cli import create as create_cmd


app = typer.Typer(help="Agent-Forge CLI root")
app.add_typer(create_cmd.app, name="create")


