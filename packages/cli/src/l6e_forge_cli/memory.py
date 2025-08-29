from __future__ import annotations

import os
import typer
from rich import print as rprint
import httpx


app = typer.Typer(help="Memory utilities (dev)")


def _api_base() -> str:
    return os.environ.get("AF_API_URL", "http://localhost:8000/api").rstrip("/")


@app.command()
def upsert(
    namespace: str = typer.Option(
        ..., "--ns", "--namespace", help="Memory namespace (e.g., agent name)"
    ),
    collection: str | None = typer.Option(
        None,
        "--collection",
        "-c",
        help="Optional collection name to target (overrides backend default)",
    ),
    key: str = typer.Option(..., "--key", help="Unique key for the entry"),
    content: str = typer.Option(..., "--content", help="Content to store"),
) -> None:
    url = f"{_api_base()}/memory/upsert"
    try:
        payload: dict[str, object] = {
            "namespace": namespace,
            "key": key,
            "content": content,
        }
        if collection:
            payload["collection"] = collection
        resp = httpx.post(url, json=payload, timeout=10.0)
        resp.raise_for_status()
        rprint("[green]Upserted memory.[/green]")
    except Exception as exc:  # noqa: BLE001
        rprint(f"[red]Failed to upsert memory:[/red] {exc}")
        raise typer.Exit(code=1)


@app.command()
def search(
    namespace: str = typer.Option(
        ..., "--ns", "--namespace", help="Memory namespace (e.g., agent name)"
    ),
    collection: str | None = typer.Option(
        None,
        "--collection",
        "-c",
        help="Optional collection name to target (overrides backend default)",
    ),
    query: str = typer.Option(..., "--query", help="Query text"),
    limit: int = typer.Option(5, "--limit", help="Max results"),
) -> None:
    url = f"{_api_base()}/memory/search"
    try:
        payload: dict[str, object] = {
            "namespace": namespace,
            "query": query,
            "limit": limit,
        }
        if collection:
            payload["collection"] = collection
        resp = httpx.post(url, json=payload, timeout=10.0)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results") or []
        if not results:
            rprint("[yellow]No results.[/yellow]")
            return
        for idx, r in enumerate(results, start=1):
            rprint(
                f"[cyan]{idx}[/cyan] score={r.get('score', 0):.3f} key={r.get('key', '')}\n  {r.get('content', '')}"
            )
    except Exception as exc:  # noqa: BLE001
        rprint(f"[red]Failed to search memory:[/red] {exc}")
        raise typer.Exit(code=1)
