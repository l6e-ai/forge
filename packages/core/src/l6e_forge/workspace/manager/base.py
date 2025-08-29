from pathlib import Path
from typing import Protocol

from l6e_forge.types.workspace import WorkspaceState, WorkspaceValidation


class IWorkspaceManager(Protocol):
    """Workspace manager interface"""

    async def create_workspace(
        self,
        path: Path,
        template: str | None = None,
        with_compose: bool = True,
        conversation_store: str | None = None,
    ) -> None:
        """Create a new workspace"""
        ...

    async def load_workspace(self, path: Path) -> WorkspaceState:
        """Load an existing workspace"""
        ...

    async def save_workspace(self, workspace_state: WorkspaceState) -> None:
        """Save workspace state"""
        ...

    async def validate_workspace(self, path: Path) -> WorkspaceValidation:
        """Validate workspace structure and configuration"""
        ...

    def list_workspaces(self) -> list[Path]:
        """List known workspaces"""
        ...
