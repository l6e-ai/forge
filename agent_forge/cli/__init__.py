from __future__ import annotations

import typer

from l6e_forge.cli import create as create_cmd


app = typer.Typer(help="l6e-forge CLI root")
app.add_typer(create_cmd.app, name="create")


