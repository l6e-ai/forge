from __future__ import annotations

from pathlib import Path
from typing import Iterable


class PromptTemplateLoader:
    """Locate and load prompt templates from filesystem.

    Search order (first found wins):
    - Absolute path
    - Provided search_paths (in order)
    - Workspace defaults (if workspace_root provided):
      workspace_root/templates,
      workspace_root/shared/prompts,
      workspace_root/agents/<agent_name>/templates (if agent_name provided)
    """

    def __init__(self, search_paths: Iterable[Path] | None = None) -> None:
        self._search_paths = [Path(p).resolve() for p in (search_paths or [])]

    def _candidate_paths(
        self,
        template_ref: str,
        workspace_root: Path | None,
        agent_name: str | None,
    ) -> list[Path]:
        ref = Path(template_ref)
        if ref.is_absolute():
            return [ref]
        cands: list[Path] = []
        # Explicit search paths
        for base in self._search_paths:
            cands.append((base / ref).resolve())
        # Workspace defaults
        if workspace_root is not None and workspace_root.exists():
            cands.append((workspace_root / "templates" / ref).resolve())
            cands.append((workspace_root / "shared" / "prompts" / ref).resolve())
            if agent_name:
                cands.append(
                    (
                        workspace_root / "agents" / agent_name / "templates" / ref
                    ).resolve()
                )
                cands.append((workspace_root / "prompts" / agent_name / ref).resolve())
            # Workspace-level prompts fallback
            cands.append((workspace_root / "prompts" / ref).resolve())
        # Fallback: relative to CWD
        cands.append(Path.cwd() / ref)
        return cands

    def load(
        self,
        template_ref: str,
        workspace_root: Path | None = None,
        agent_name: str | None = None,
    ) -> str:
        for path in self._candidate_paths(template_ref, workspace_root, agent_name):
            try:
                if path.exists() and path.is_file():
                    return path.read_text(encoding="utf-8")
            except Exception:
                continue
        raise FileNotFoundError(f"Prompt template not found: {template_ref}")
