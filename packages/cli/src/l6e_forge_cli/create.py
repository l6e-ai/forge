from __future__ import annotations

from pathlib import Path

import typer
from rich import print as rprint

from l6e_forge.workspace.template_engine.jinja import JinjaTemplateEngine
from l6e_forge_cli.templates.specs import get_template_spec

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
    include_compose: bool = typer.Option(
        True,
        "--include-compose/--no-include-compose",
        help="Generate/append compose with memory provider.",
    ),
    memory_provider: str = typer.Option(
        "qdrant",
        "--memory-provider",
        help="Default memory provider to include in compose (qdrant|memory)",
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
        variables = {
            "name": name,
            "provider": provider,
            "model": model,
            "endpoint": provider_endpoint or "",
        }
        import asyncio as _asyncio

        for tf in spec.files:
            rendered = _asyncio.run(
                engine.render_template(tf.content.strip(), variables)
            )
            (target / tf.path).write_text(rendered, encoding=tf.encoding)
        # Create a default templates/ with chat.j2
        try:
            tdir = target / "templates"
            tdir.mkdir(parents=True, exist_ok=True)
            default_chat = (
                "{%- set k = 6 -%}\n"
                "You are an assistant.\n\n"
                "Recent conversation (last {{ k }}):\n"
                "{%- for m in history_k(k) %}\n"
                "- [{{ m.role }}] {{ m.content }}\n"
                "{%- endfor %}\n\n"
                "{%- if recall %}\n"
                "Related memory:\n"
                "{{ recall }}\n\n"
                "{%- endif %}\n"
                "User says: {{ user_input }}\n"
                "Provide a concise answer.\n"
            )
            (tdir / "chat.j2").write_text(default_chat, encoding="utf-8")
        except Exception:
            pass
        rprint(f"[green]Created agent at {target}[/green]")
        # Optionally write/append compose with memory provider
        if include_compose:
            try:
                from l6e_forge.infra.compose import (
                    ComposeTemplateService,
                    ComposeServiceSpec,
                )

                svc = ComposeTemplateService()
                ui_context: dict = {}
                workspace_ui_dir = root / "ui"
                if workspace_ui_dir.exists():
                    ui_context["ui_mount"] = str(workspace_ui_dir.resolve())
                services = [
                    ComposeServiceSpec(name="monitor"),
                    ComposeServiceSpec(
                        name="api", context={"memory_provider": memory_provider}
                    ),
                    ComposeServiceSpec(name="ui", context=ui_context),
                ]
                if memory_provider == "qdrant":
                    services.append(ComposeServiceSpec(name="qdrant"))

                compose_path = root / "docker-compose.yml"
                if compose_path.exists():
                    existing = compose_path.read_text(encoding="utf-8")
                    merged = _asyncio.run(svc.merge(existing, services))
                    if merged != existing:
                        compose_path.write_text(merged, encoding="utf-8")
                        rprint(
                            "[green]Updated docker-compose.yml with missing services.[/green]"
                        )
                    else:
                        rprint(
                            "[green]docker-compose.yml already includes required services.[/green]"
                        )
                else:
                    compose_text = _asyncio.run(svc.generate(services))
                    compose_path.write_text(compose_text, encoding="utf-8")
                    rprint(
                        "[green]Wrote docker-compose.yml with memory provider.[/green]"
                    )
            except Exception as exc:
                rprint(f"[yellow]Compose generation skipped:[/yellow] {exc}")
    except FileExistsError:
        rprint(f"[red]Agent already exists: {target}[/red]")
        raise typer.Exit(code=1)


def main() -> None:
    app()
