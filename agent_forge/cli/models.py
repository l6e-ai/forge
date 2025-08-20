from __future__ import annotations

import typer
from rich import print as rprint
from pathlib import Path
from rich.table import Table

from agent_forge.models.managers.ollama import OllamaModelManager
from agent_forge.models.managers.lmstudio import LMStudioModelManager
from agent_forge.models.auto import (
    get_system_profile,
    AutoHints,
    recommend_models,
    ensure_ollama_models,
    apply_recommendations_to_agent_config,
)


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


@app.command()
def doctor() -> None:
    """Show system profile relevant to local model selection."""
    sys = get_system_profile()
    rprint("[cyan]System Profile[/cyan]")
    rprint(f"  OS: {sys.os}")
    rprint(f"  CPU cores: {sys.cpu_cores}")
    rprint(f"  RAM: {sys.ram_gb} GB")
    rprint(f"  GPU: {'yes' if sys.has_gpu else 'no'}  VRAM: {sys.vram_gb} GB")
    rprint(f"  Internet: {'yes' if sys.has_internet else 'no'}")
    rprint(f"  Ollama CLI: {'yes' if sys.has_ollama else 'no'}")


@app.command()
def bootstrap(
    agent: str = typer.Argument(..., help="Agent directory (contains config.toml)"),
    provider: str = typer.Option("ollama", "--provider", help="Provider to bootstrap (ollama only for now)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Only print recommendations"),
) -> None:
    """Auto-select and (optionally) pull recommended local models for an agent."""
    sys = get_system_profile()
    hints = AutoHints(provider_order=[provider])
    recs = recommend_models(sys, hints)
    rprint("[cyan]Recommended Models[/cyan]")
    for k, v in recs.items():
        rprint(f"  {k}: {v}")
    if dry_run:
        return
    if provider == "ollama":
        recs = ensure_ollama_models(recs)
        apply_recommendations_to_agent_config(Path(agent), provider, recs)
        # Show a concise confirmation of config
        rprint("[green]Models ready and agent config updated.[/green]")
        try:
            cfg_path = Path(agent) / "config.toml"
            text = cfg_path.read_text(encoding="utf-8")
            # Print only the model and memory sections for clarity
            snippet = "\n".join([ln for ln in text.splitlines() if ln.strip().startswith("[model]") or ln.strip().startswith("provider =") or ln.strip().startswith("model =") or ln.strip().startswith("[memory]") or ln.strip().startswith("embedding_model")])
            if snippet:
                rprint("\n[cyan]Updated config[/cyan]\n" + snippet)
        except Exception:
            pass
    else:
        rprint(f"[yellow]Provider not supported yet: {provider}[/yellow]")


def main() -> None:
    app()


