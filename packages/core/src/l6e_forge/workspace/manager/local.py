from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import List

from l6e_forge.workspace.manager.base import IWorkspaceManager
from l6e_forge.types.workspace import (
    WorkspaceState,
    WorkspaceValidation,
)


class LocalWorkspaceManager(IWorkspaceManager):
    """Local filesystem implementation of `IWorkspaceManager`.

    Keeps behavior minimal to support MVP commands: `forge init` and `forge list`.
    """

    async def create_workspace(
        self,
        path: Path,
        template: str | None = None,
        with_compose: bool = True,
        conversation_store: str | None = None,
    ) -> None:
        root = Path(path).expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)

        # Standard structure (align with docs: keep .forge for internal data)
        agents_dir = root / "agents"
        internal_dir = root / ".forge"
        logs_dir = internal_dir / "logs"
        data_dir = internal_dir / "data"
        ui_dir = internal_dir / "ui"
        shared_dir = root / "shared"
        tools_dir = root / "tools"
        templates_dir = root / "templates"
        prompts_dir = root / "prompts"

        for d in (
            agents_dir,
            logs_dir,
            data_dir,
            shared_dir,
            tools_dir,
            ui_dir,
            templates_dir,
            prompts_dir,
        ):
            d.mkdir(parents=True, exist_ok=True)

        # Create default forge.toml if it doesn't exist
        config_file = root / "forge.toml"
        if not config_file.exists():
            config_file.write_text(
                """
# l6e-forge Workspace Configuration

[workspace]
name = "{name}"
version = "0.1.0"

[runtime]
hot_reload = true
""".strip().format(name=root.name),
                encoding="utf-8",
            )

        # Generate a docker-compose file using the ComposeTemplateService (preferred over copying a static template)
        if with_compose:
            try:
                from l6e_forge.infra.compose import (
                    ComposeTemplateService,
                    ComposeServiceSpec,
                )

                target_cp = root / "docker-compose.yml"
                if not target_cp.exists():
                    svc = ComposeTemplateService()
                    ui_context: dict = {}
                    workspace_ui_dir = root / "ui"
                    if workspace_ui_dir.exists():
                        ui_context["ui_mount"] = str(workspace_ui_dir.resolve())

                    services = [
                        ComposeServiceSpec(name="monitor"),
                        ComposeServiceSpec(name="api", context={}),
                        ComposeServiceSpec(name="ui", context=ui_context),
                    ]
                    # Configure conversation store; default to postgres
                    if (conversation_store or "postgres").lower() == "postgres":
                        services.insert(0, ComposeServiceSpec(name="postgres"))
                        # Ensure AF_DB_URL is templated via api context (defaults ok)
                        services = [
                            ComposeServiceSpec(
                                name=s.name,
                                context=(
                                    s.context
                                    | {
                                        "db_url": "postgresql://forge:forge@postgres:5432/forge"
                                    }
                                    if s.name == "api"
                                    else s.context
                                ),
                            )
                            for s in services
                        ]
                        # Create migrations directory with initial file
                        mig_dir = root / "migrations"
                        mig_dir.mkdir(parents=True, exist_ok=True)
                        (mig_dir / "0001_init.sql").write_text(
                            (
                                """
-- Create schema and tables for conversation/message persistence
create schema if not exists forge;

create table if not exists forge.conversations (
  conversation_id uuid primary key,
  agent_id text,
  user_id text,
  started_at timestamptz default now(),
  last_activity timestamptz default now(),
  message_count integer default 0
);

create table if not exists forge.messages (
  message_id uuid primary key,
  conversation_id uuid not null references forge.conversations(conversation_id) on delete cascade,
  role text not null,
  content text not null,
  timestamp timestamptz not null default now(),
  metadata jsonb default '{}'::jsonb
);

create index if not exists idx_messages_conversation_ts on forge.messages (conversation_id, timestamp desc);
"""
                            ).strip(),
                            encoding="utf-8",
                        )
                    compose_text = await svc.generate(services)
                    target_cp.write_text(compose_text, encoding="utf-8")
            except Exception:
                # Non-fatal if compose generation fails
                pass

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
            warnings.append(
                "Missing 'forge.toml'; run 'forge init <workspace>' to create one."
            )

        if not internal_dir.exists():
            warnings.append(
                "Missing '.forge/' internal directory; it will be created on demand."
            )

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
