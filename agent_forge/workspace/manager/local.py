from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import List

from agent_forge.workspace.manager.base import IWorkspaceManager
from agent_forge.types.workspace import (
    WorkspaceState,
    WorkspaceValidation,
)


class LocalWorkspaceManager(IWorkspaceManager):
    """Local filesystem implementation of `IWorkspaceManager`.

    Keeps behavior minimal to support MVP commands: `forge init` and `forge list`.
    """

    async def create_workspace(self, path: Path, template: str | None = None) -> None:
        root = Path(path).expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)

        # Standard structure (align with docs: keep .forge for internal data)
        agents_dir = root / "agents"
        internal_dir = root / ".forge"
        logs_dir = internal_dir / "logs"
        data_dir = internal_dir / "data"
        shared_dir = root / "shared"
        tools_dir = root / "tools"

        for d in (agents_dir, logs_dir, data_dir, shared_dir, tools_dir):
            d.mkdir(parents=True, exist_ok=True)

        # Create default forge.toml if it doesn't exist
        config_file = root / "forge.toml"
        if not config_file.exists():
            config_file.write_text(
                """
# Agent-Forge Workspace Configuration

[workspace]
name = "{name}"
version = "0.1.0"

[runtime]
hot_reload = true
""".strip().format(name=root.name),
                encoding="utf-8",
            )

        # Optionally scaffold a basic example agent if a template is requested later
        _ = template  # not used in MVP

    async def load_workspace(self, path: Path) -> WorkspaceState:
        root = Path(path).expanduser().resolve()
        agents_dir = root / "agents"

        agent_names: List[str] = []
        if agents_dir.exists():
            for p in agents_dir.iterdir():
                if p.is_dir():
                    agent_names.append(p.name)

        return WorkspaceState(
            workspace_id=str(root),
            status="active" if root.exists() else "error",
            agent_count=len(agent_names),
            active_agents=agent_names,
        )

    async def save_workspace(self, workspace_state: WorkspaceState) -> None:
        # MVP: no-op persistence; config lives in forge.toml
        _ = asdict(workspace_state)

    async def validate_workspace(self, path: Path) -> WorkspaceValidation:
        root = Path(path).expanduser().resolve()
        agents_dir = root / "agents"
        config_file = root / "forge.toml"
        internal_dir = root / ".forge"

        errors: List[str] = []
        warnings: List[str] = []

        if not root.exists():
            errors.append(f"Workspace path does not exist: {root}")

        if not agents_dir.exists():
            warnings.append("Missing 'agents/' directory; creating it is recommended.")

        if not config_file.exists():
            warnings.append("Missing 'forge.toml'; run 'forge init <workspace>' to create one.")

        if not internal_dir.exists():
            warnings.append("Missing '.forge/' internal directory; it will be created on demand.")

        is_valid = len(errors) == 0
        return WorkspaceValidation(
            workspace_path=root,
            is_valid=is_valid,
            structure_valid=is_valid,
            config_valid=config_file.exists(),
            agents_valid=agents_dir.exists(),
            dependencies_satisfied=True,
            errors=errors,
            warnings=warnings,
        )

    def list_workspaces(self) -> list[Path]:
        # MVP: return just the current directory if it looks like a workspace
        cwd = Path.cwd().resolve()
        if (cwd / "forge.toml").exists() and (cwd / "agents").exists():
            return [cwd]
        return []


