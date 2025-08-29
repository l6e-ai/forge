from __future__ import annotations

from pathlib import Path
from typing import Callable

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from rich import print as rprint


class DevEventHandler(FileSystemEventHandler):
    def __init__(
        self, agents_dir: Path, on_agent_changed: Callable[[str], None]
    ) -> None:
        super().__init__()
        self.agents_dir = agents_dir.resolve()
        self.on_agent_changed = on_agent_changed

    def on_any_event(self, event: FileSystemEvent) -> None:  # noqa: D401
        try:
            src = getattr(event, "src_path", None)
            dest = getattr(event, "dest_path", None)
            if event.event_type == "modified":
                rprint(f"[blue]Modified:[/blue] {src}")
            elif event.event_type == "created":
                rprint(f"[green]Created:[/green] {src}")
            elif event.event_type == "deleted":
                rprint(f"[red]Deleted:[/red] {src}")
            elif event.event_type == "moved":
                rprint(f"[magenta]Moved:[/magenta] {src} -> {dest}")

            path_str = src or dest
            if path_str:
                changed_path = Path(path_str).resolve()
                if (
                    changed_path.suffix == ".py"
                    and self.agents_dir in changed_path.parents
                ):
                    rel = changed_path.relative_to(self.agents_dir)
                    agent_name = rel.parts[0] if rel.parts else None
                    if agent_name:
                        self.on_agent_changed(agent_name)
        except Exception:  # noqa: BLE001
            pass
