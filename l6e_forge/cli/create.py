from __future__ import annotations

from pathlib import Path

import typer
from rich import print as rprint

from l6e_forge.cli.templates import AGENT_ECHO_PY, AGENT_OLLAMA_PY, CONFIG_TOML
from l6e_forge.workspace.template_engine.jinja import JinjaTemplateEngine
from l6e_forge.cli.templates.specs import get_template_spec

app = typer.Typer(help="Agent creation commands")


@app.command()
def agent(
    name: str = typer.Argument(..., help="Agent name"),
    workspace: str = typer.Option(".", help="Workspace root path"),
    provider: str = typer.Option(
        "ollama",
        "--provider",
        help="Model provider to scaffold with (e.g., 'ollama'). Others will default to echo for now.",
    ),
    model: str = typer.Option(
        "llama3.2:3b",
        "--model",
        help="Default model to use for the scaffold when provider is model-based.",
    ),
    provider_endpoint: str | None = typer.Option(
        None,
        "--provider-endpoint",
        help="Optional provider endpoint (e.g., http://localhost:11434 for Ollama)",
    ),
    template: str = typer.Option(
        "assistant",
        "--template",
        help="Template to use (e.g., 'basic', 'assistant'). Provider-specific variants are resolved automatically.",
    ),
):
    """Scaffold a minimal agent directory."""
    root = Path(workspace).resolve()
    agents_dir = root / "agents"
    target = agents_dir / name
    try:
        target.mkdir(parents=True, exist_ok=False)
        spec = get_template_spec(template, provider)
        engine = JinjaTemplateEngine()
        variables = {"name": name, "provider": provider, "model": model, "endpoint": provider_endpoint or ""}
        import asyncio as _asyncio
        for tf in spec.files:
            rendered = _asyncio.run(engine.render_template(tf.content.strip(), variables))
            (target / tf.path).write_text(rendered, encoding=tf.encoding)
        rprint(f"[green]Created agent at {target}[/green]")
    except FileExistsError:
        rprint(f"[red]Agent already exists: {target}[/red]")
        raise typer.Exit(code=1)


def main() -> None:
    app()


