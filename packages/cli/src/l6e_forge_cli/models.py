from __future__ import annotations

import os
import typer
from rich import print as rprint
from pathlib import Path
from rich.table import Table

try:
    from questionary import select as qselect  # type: ignore
except Exception:  # pragma: no cover
    qselect = None  # type: ignore

from l6e_forge.models.managers.base import IModelManager
from l6e_forge.models.managers.ollama import OllamaModelManager
from l6e_forge.models.managers.lmstudio import LMStudioModelManager
from l6e_forge.models.auto import (
    get_system_profile,
    AutoHints,
    AutoHintQuality,
    AutoHintQuantization,
    ensure_ollama_models,
    apply_recommendations_to_agent_config,
    suggest_models,
)


app = typer.Typer(help="Model utilities")


@app.command(name="list")
def list_command(
    provider: str | None = typer.Option(
        None, "--provider", help="Provider: ollama|lmstudio|all (default: all)"
    ),
    endpoint: str | None = typer.Option(
        None,
        "--endpoint",
        help="Provider endpoint override (applies only when a single provider is specified)",
    ),
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
    mgr: IModelManager | None = None
    for p in providers:
        if p == "ollama":
            default_ep = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
            mgr = (
                OllamaModelManager(endpoint=endpoint or default_ep)
                if len(providers) == 1
                else OllamaModelManager(default_ep)
            )
        elif p == "lmstudio":
            default_ep = os.environ.get("LMSTUDIO_HOST", "http://localhost:1234/v1")
            mgr = (
                LMStudioModelManager(endpoint=endpoint or default_ep)
                if len(providers) == 1
                else LMStudioModelManager(default_ep)
            )
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
            table.add_row(
                p,
                s.model_name,
                str(s.context_length),
                "yes" if s.supports_streaming else "no",
            )

    if not any_rows:
        rprint(
            "[yellow]No models found. Ensure providers are running and models are available.[/yellow]"
        )
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
    provider_order: str = typer.Option(
        "ollama,lmstudio",
        "--provider-order",
        help="Preferred providers order (comma-separated)",
    ),
    quality: str = typer.Option("balanced", "--quality", help="speed|balanced|quality"),
    quant: str = typer.Option("auto", "--quant", help="auto|q4|q5|q8|mxfp4|8bit"),
    top_n: int = typer.Option(5, "--top", help="Number of options to show"),
    interactive: bool = typer.Option(
        True,
        "--interactive/--no-interactive",
        help="Prompt to choose a model (default: interactive)",
    ),
    accept_best: bool = typer.Option(
        False, "--accept-best", help="Skip prompt and accept the top suggestion"
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Only print recommendations"),
) -> None:
    """Suggest, select, and configure local models; pulls for Ollama when needed."""
    # Early exit if the agent directory is invalid
    agent_dir = Path(agent)
    if not agent_dir.exists() or not agent_dir.is_dir():
        rprint(f"[red]Agent directory not found:[/red] {agent_dir}")
        raise typer.Exit(code=1)
    if not (agent_dir / "config.toml").exists():
        rprint(f"[red]Missing config.toml in agent directory:[/red] {agent_dir}")
        raise typer.Exit(code=1)

    try:
        quality = AutoHintQuality(quality)
    except ValueError:
        rprint(
            f"[yellow]Invalid quality: {quality}. Must be speed, balanced, or quality.[/yellow]"
        )
        raise typer.Exit(code=1)
    try:
        quant = AutoHintQuantization(quant)
    except ValueError:
        rprint(
            f"[yellow]Invalid quantization: {quant}. Must be auto, q4, q5, q8, mxfp4, or 8bit.[/yellow]"
        )
        raise typer.Exit(code=1)

    sys = get_system_profile()
    order = [p.strip() for p in provider_order.split(",") if p.strip()]
    hints = AutoHints(provider_order=order, quality=quality, quantization=quant)

    suggestions = suggest_models(sys, hints, top_n=top_n)
    if not suggestions:
        rprint(
            "[yellow]No model suggestions found. Ensure providers are running and try again.[/yellow]"
        )
        raise typer.Exit(code=1)

    table = Table(title="Model Suggestions")
    table.add_column("#")
    table.add_column("Model")
    table.add_column("Provider")
    table.add_column("Tag")
    table.add_column("Est. Mem (GB)")
    table.add_column("% of VRAM/RAM")
    table.add_column("Fits Local")
    table.add_column("Source")
    table.add_column("Installed")
    table.add_column("Notes")
    for idx, s in enumerate(suggestions):
        table.add_row(
            str(idx),
            s.entry.display_name,
            s.provider,
            s.provider_tag or "-",
            f"{s.est_memory_gb:.1f}",
            f"{s.mem_pct}% of {s.mem_capacity_type.upper()} ({s.mem_capacity_gb:.1f} GB)",
            "yes" if s.fits_local else "maybe",
            s.estimate_source,
            "yes" if s.is_installed else "no",
            s.reason,
        )
    rprint(table)

    if dry_run:
        return

    # Non-interactive environments: force accept_best
    import sys as _sys

    if not (_sys.stdin.isatty() and _sys.stdout.isatty()):
        interactive = False
        if not accept_best:
            accept_best = True

    choice_idx = 0
    if interactive and not accept_best:
        if qselect is not None:
            # Build choices like "0) Provider • Tag • Model"
            items = [
                (
                    f"{i}) {s.provider} • {s.provider_tag or '-'} • {s.entry.display_name}  [{s.est_memory_gb:.1f} GB]",
                    i,
                )
                for i, s in enumerate(suggestions)
            ]
            try:
                choice_idx = qselect(
                    "Select a model:",
                    choices=[{"name": name, "value": idx} for name, idx in items],
                ).ask()  # type: ignore
                if choice_idx is None:
                    choice_idx = 0
            except Exception:
                choice_idx = 0
        else:
            try:
                choice_idx = int(typer.prompt("Select a model by index", default="0"))
            except Exception:
                choice_idx = 0
    elif not accept_best and not interactive:
        rprint(
            "[yellow]Tip:[/yellow] re-run with --interactive to choose or --accept-best to auto-select the top option."
        )
        return

    choice_idx = max(0, min(choice_idx, len(suggestions) - 1))
    chosen = suggestions[choice_idx]

    recs = {
        "chat": chosen.provider_tag or chosen.entry.model_key,
        "embedding": "nomic-embed-text:latest",
    }
    if chosen.provider == "ollama":
        recs = ensure_ollama_models(recs, endpoint=os.environ.get("OLLAMA_HOST"))
    apply_recommendations_to_agent_config(Path(agent), chosen.provider, recs)

    rprint("[green]Agent config updated.[/green]")
    try:
        cfg_path = Path(agent) / "config.toml"
        text = cfg_path.read_text(encoding="utf-8")
        snippet = "\n".join(
            [
                ln
                for ln in text.splitlines()
                if ln.strip().startswith("[model]")
                or ln.strip().startswith("provider =")
                or ln.strip().startswith("model =")
                or ln.strip().startswith("[memory]")
                or ln.strip().startswith("embedding_model")
            ]
        )
        if snippet:
            rprint("\n[cyan]Updated config[/cyan]\n" + snippet)
    except Exception:
        pass


@app.command()
def suggest(
    provider: str | None = typer.Option(
        None,
        "--provider",
        help="Preferred provider order, comma-separated (e.g., ollama,lmstudio)",
    ),
    quality: str = typer.Option("balanced", "--quality", help="speed|balanced|quality"),
    top_n: int = typer.Option(5, "--top", help="Number of options to show"),
    quant: str = typer.Option(
        "auto", "--quant", help="Quantization assumption: auto|q4|q5|q8|mxfp4|8bit"
    ),
) -> None:
    """Show suggested chat models with estimated memory usage and fit.

    This presents a short list with our estimated memory (including overhead) so users can pick.
    """

    try:
        quality = AutoHintQuality(quality)
    except ValueError:
        rprint(
            f"[yellow]Invalid quality: {quality}. Must be speed, balanced, or quality.[/yellow]"
        )
        raise typer.Exit(code=1)
    try:
        quant = AutoHintQuantization(quant)
    except ValueError:
        rprint(
            f"[yellow]Invalid quantization: {quant}. Must be auto, q4, q5, q8, mxfp4, or 8bit.[/yellow]"
        )
        raise typer.Exit(code=1)

    sys = get_system_profile()
    order = [p.strip() for p in (provider or "ollama,lmstudio").split(",") if p.strip()]
    hints = AutoHints(
        provider_order=order,
        quality=quality,
        quantization=quant,
    )
    suggestions = suggest_models(sys, hints, top_n=top_n)

    table = Table(title="Suggested Chat Models")
    table.add_column("Model")
    table.add_column("Provider")
    table.add_column("Tag")
    table.add_column("Est. Mem (GB)")
    table.add_column("% of VRAM/RAM")
    table.add_column("Fits Local")
    table.add_column("Source")
    table.add_column("Installed")
    table.add_column("Notes")

    if not suggestions:
        rprint(
            "[yellow]No suggestions available. Ensure providers are running.[/yellow]"
        )
        raise typer.Exit(code=0)

    for s in suggestions:
        table.add_row(
            s.entry.display_name,
            s.provider,
            s.provider_tag or "-",
            f"{s.est_memory_gb:.1f}",
            f"{s.mem_pct}% of {s.mem_capacity_type.upper()} ({s.mem_capacity_gb:.1f} GB)",
            "yes" if s.fits_local else "maybe",
            s.estimate_source,
            "yes" if s.is_installed else "no",
            s.reason,
        )
    rprint(table)


def main() -> None:
    app()
