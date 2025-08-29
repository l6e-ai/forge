from __future__ import annotations

from pathlib import Path
import importlib.util
from types import ModuleType
import sys
from rich import print as rprint


class AgentReloader:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.agent_modules: dict[str, ModuleType] = {}

    def _module_name(self, agent_name: str) -> str:
        return f"l6e_forge_dev.{agent_name}"

    def load_all(self) -> None:
        if not self.base_dir.exists():
            return
        for path in self.base_dir.iterdir():
            if path.is_dir():
                self.load_agent(path)

    def load_agent(self, agent_dir: Path) -> None:
        agent_name = agent_dir.name
        agent_file = agent_dir / "agent.py"
        if not agent_file.exists():
            return
        try:
            module_name = self._module_name(agent_name)
            spec = importlib.util.spec_from_file_location(module_name, agent_file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                self.agent_modules[agent_name] = module
                rprint(f"[bold cyan]Loaded agent:[/bold cyan] {agent_name}")
        except Exception as exc:  # noqa: BLE001
            rprint(f"[red]Failed to load agent {agent_name}:[/red] {exc}")

    def reload_agent(self, agent_dir: Path) -> None:
        self.load_agent(agent_dir)
