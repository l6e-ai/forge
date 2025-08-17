from __future__ import annotations

import typer
from rich import print as rprint
from rich.table import Table

from agent_forge.cli.templates.specs import get_template_spec


app = typer.Typer(help="Template utilities")


@app.command()
def list() -> None:  # noqa: A003 - CLI verb
    """List available templates and supported providers."""
    templates = ["basic", "assistant"]
    providers = ["local", "ollama", "lmstudio"]

    table = Table(title="Templates")
    table.add_column("Template")
    table.add_column("Providers")
    table.add_column("Description")

    for tmpl in templates:
        supported: list[str] = []
        description = ""
        for prov in providers:
            try:
                spec = get_template_spec(tmpl, prov)
                supported.append(prov)
                # capture description from first successful spec
                if not description:
                    description = spec.description
            except Exception:
                continue
        if supported:
            table.add_row(tmpl, ", ".join(supported), description or "")

    rprint(table)


def main() -> None:
    app()


