from __future__ import annotations

import typer
from rich import print as rprint
from rich.table import Table

from agent_forge.models.managers.ollama import OllamaModelManager
from agent_forge.models.managers.lmstudio import LMStudioModelManager


app = typer.Typer(help="Model utilities")


@app.command()
def list(
    provider: str | None = typer.Option(None, "--provider", help="Provider: ollama|lmstudio|all (default: all)"),
    endpoint: str | None = typer.Option(None, "--endpoint", help="Provider endpoint override (applies only when a single provider is specified)"),
) -> None:  # noqa: A003
    """List available models. Defaults to listing all supported providers."""
    prov = (provider or "all").lower()
    providers = ["ollama", "lmstudio"] if prov in ("all", "", None) else [prov]

    table = Table(title="Models")
    table.add_column("Provider")
    table.add_column("Name")
    table.add_column("Context")
    table.add_column("Supports Streaming")

    any_rows = False
    for p in providers:
        if p == "ollama":
            mgr = OllamaModelManager(endpoint=endpoint or "http://localhost:11434") if len(providers) == 1 else OllamaModelManager("http://localhost:11434")
        elif p == "lmstudio":
            mgr = LMStudioModelManager(endpoint=endpoint or "http://localhost:1234/v1") if len(providers) == 1 else LMStudioModelManager("http://localhost:1234/v1")
        else:
            rprint(f"[yellow]Skipping unsupported provider: {p}[/yellow]")
            continue

        try:
            specs = mgr.list_available_models()
        except Exception as exc:  # noqa: BLE001
            rprint(f"[red]Failed to list models for {p}:[/red] {exc}")
            continue

        for s in specs:
            any_rows = True
            table.add_row(p, s.model_name, str(s.context_length), "yes" if s.supports_streaming else "no")

    if not any_rows:
        rprint("[yellow]No models found. Ensure providers are running and models are available.[/yellow]")
        raise typer.Exit(code=0)

    rprint(table)


def main() -> None:
    app()


