from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Iterable

from rich import print as rprint
from watchdog.observers import Observer

from l6e_forge.dev.reloader import AgentReloader
from l6e_forge.dev.handler import DevEventHandler
from l6e_forge.runtime.local import LocalRuntime
import asyncio
from l6e_forge.config_managers.toml import TomlConfigManager
from l6e_forge.runtime.monitoring import get_monitoring


class DevService:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.agents_dir = self.root / "agents"
        self.config_file = self.root / "forge.toml"
        self.reloader = AgentReloader(self.agents_dir)
        self.observer = Observer()
        self.runtime = LocalRuntime()
        self._agent_ids: dict[str, str] = {}
        self._last_reload_ts: dict[str, float] = {}
        self._debounce_seconds: float = 0.25
        self._hot_reload_enabled: bool = True
        # Load runtime config if present
        try:
            cfg = TomlConfigManager()
            data = asyncio.run(cfg.load_config(self.config_file))
            _ = data
            db = cfg.get_config_value("runtime.debounce_seconds")
            if isinstance(db, (int, float)):
                self._debounce_seconds = max(0.0, float(db))
            hr = cfg.get_config_value("runtime.hot_reload")
            if isinstance(hr, bool):
                self._hot_reload_enabled = hr
        except Exception:
            pass

    def start(
        self, run_for: float | None = None, test_touch: Iterable[str] | None = None
    ) -> int:
        if not (
            (self.root / "forge.toml").exists() and (self.root / "agents").exists()
        ):
            rprint(f"[red]Not a workspace: {self.root}[/red]")
            return 1

        self.reloader.load_all()
        # Register all agents with runtime
        self._register_all_agents()
        # Best-effort start monitoring web UI in background (dev only)
        # If AF_MONITOR_URL is set, we assume a remote UI is running and skip local UI
        if not os.environ.get("AF_MONITOR_URL"):
            try:
                asyncio.get_event_loop()
            except RuntimeError:
                asyncio.set_event_loop(asyncio.new_event_loop())
            try:
                # Spawn a background task to run the server without blocking
                import threading

                t = threading.Thread(
                    target=self._run_monitoring_ui, args=(), daemon=True
                )
                t.start()
            except Exception:
                pass
        handler = DevEventHandler(
            self.agents_dir, on_agent_changed=self._on_agent_changed
        )
        self.observer.schedule(handler, str(self.agents_dir), recursive=True)
        self.observer.schedule(handler, str(self.root), recursive=False)

        rprint(f"[cyan]Watching:[/cyan] {self.agents_dir}")
        rprint(f"[cyan]Watching:[/cyan] {self.config_file}")
        rprint(
            f"[green]Dev mode started (hot_reload={self._hot_reload_enabled}, debounce={self._debounce_seconds}s). Press Ctrl+C to stop.[/green]"
        )

        try:
            self.observer.start()
            if test_touch:
                time.sleep(0.1)
                for p in test_touch:
                    try:
                        pp = Path(p)
                        if pp.exists():
                            now = time.time()
                            os.utime(pp, (now, now))
                    except Exception:  # noqa: BLE001
                        pass
            if run_for is not None:
                time.sleep(max(0.0, float(run_for)))
            else:
                while True:
                    time.sleep(0.5)
        except KeyboardInterrupt:
            rprint("[yellow]Stopping dev mode...[/yellow]")
        finally:
            self.observer.stop()
            self.observer.join(timeout=2.0)
        return 0

    def _on_agent_changed(self, agent_name: str) -> None:
        if not self._hot_reload_enabled:
            return
        # Debounce rapid successive events for the same agent
        now = time.monotonic()
        last = self._last_reload_ts.get(agent_name, 0.0)
        if now - last < self._debounce_seconds:
            return
        self._last_reload_ts[agent_name] = now

        self.reloader.reload_agent(self.agents_dir / agent_name)
        rprint(f"[bold green]Reloaded agent:[/bold green] {agent_name}")
        # Re-register agent with runtime
        try:
            self._register_agent(agent_name)
        except Exception as exc:  # noqa: BLE001
            rprint(f"[red]Failed to re-register agent {agent_name}:[/red] {exc}")

    def _register_all_agents(self) -> None:
        if not self.agents_dir.exists():
            return
        for path in self.agents_dir.iterdir():
            if path.is_dir():
                if not (path / "agent.py").exists():
                    continue
                try:
                    self._register_agent(path.name)
                except Exception as exc:  # noqa: BLE001
                    rprint(f"[red]Failed to register agent {path.name}:[/red] {exc}")

    def _register_agent(self, agent_name: str) -> None:
        agent_dir = self.agents_dir / agent_name

        async def _run():
            # Unregister previous if exists

            prev = self._agent_ids.get(agent_name)
            if prev:
                try:
                    await self.runtime.unregister_agent(uuid_from_str(prev))
                except Exception:
                    pass
            new_id = await self.runtime.register_agent(agent_dir)
            self._agent_ids[agent_name] = str(new_id)

        def uuid_from_str(s: str):
            import uuid as _uuid

            return _uuid.UUID(s)

        asyncio.run(_run())
        rprint(f"[bold cyan]Registered agent:[/bold cyan] {agent_name}")

    def _run_monitoring_ui(self) -> None:
        """Run the FastAPI dev monitoring server on localhost:8123.

        Runs in a background thread so that file watching continues.
        """
        try:
            from l6e_forge.web.monitor.app import create_app
            import uvicorn

            app = create_app(get_monitoring())
            # If port is busy, uvicorn may call sys.exit(1) which raises SystemExit
            try:
                uvicorn.run(app, host="0.0.0.0", port=8321, log_level="warning")
            except BaseException as exc:  # catch SystemExit as well
                try:
                    rprint(f"[yellow]Monitoring UI not started:[/yellow] {exc}")
                except Exception:
                    pass
        except Exception:
            # Swallow import or other unexpected errors silently in dev background
            pass
