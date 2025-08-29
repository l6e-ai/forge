from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import asyncio

from l6e_forge.tools.base import ITool
from l6e_forge.types.tool import ToolContext, ToolResult


@dataclass
class FilesystemTool(ITool):
    """Basic filesystem operations scoped to the agent workspace.

    Supported operations via the `operation` parameter:
    - read_file: read text content of a file
    - write_file: write text content to a file (creates parents)
    - list_dir: list directory entries (files and directories)
    """

    name: str = "filesystem"
    description: str = "Perform basic filesystem operations within the workspace"
    category: str = "system"
    version: str = "0.1.0"

    def get_parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["read_file", "write_file", "list_dir"],
                },
                "path": {"type": "string", "description": "Path relative to workspace"},
                "content": {"type": "string", "description": "Content for write_file"},
            },
            "required": ["operation", "path"],
            "additionalProperties": False,
        }

    def get_return_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string"},
                "path": {"type": "string"},
                "data": {},
            },
            "required": ["operation", "path"],
        }

    async def validate_parameters(self, parameters: dict[str, Any]) -> bool:
        op = parameters.get("operation")
        if op not in {"read_file", "write_file", "list_dir"}:
            return False
        path = parameters.get("path")
        return isinstance(path, str) and len(path) > 0

    async def initialize(self) -> None:  # pragma: no cover - no-op
        return None

    async def cleanup(self) -> None:  # pragma: no cover - no-op
        return None

    async def execute(
        self, parameters: dict[str, Any], context: ToolContext
    ) -> ToolResult:
        if not await self.validate_parameters(parameters):
            return ToolResult(success=False, error_message="Invalid parameters")

        operation: str = parameters["operation"]
        rel_path = parameters["path"]
        content: str | None = parameters.get("content")

        base = context.workspace_path
        try:
            target = (base / rel_path).resolve()
        except Exception:
            return ToolResult(success=False, error_message="Invalid path")

        # Enforce sandbox: path must be within allowed_paths or workspace
        if context.allowed_paths:
            allowed = any(
                str(target).startswith(str(Path(p).resolve()))
                for p in context.allowed_paths
            )
        else:
            allowed = str(target).startswith(str(base.resolve()))
        denied = any(
            str(target).startswith(str(Path(p).resolve())) for p in context.denied_paths
        )
        if not allowed or denied:
            return ToolResult(
                success=False, error_message="Access to path is not allowed"
            )

        try:
            if operation == "read_file":
                if not target.exists() or not target.is_file():
                    return ToolResult(
                        success=False, error_message="File does not exist"
                    )

                def _read() -> str:
                    return target.read_text(encoding="utf-8")

                text = await asyncio.to_thread(_read)
                data = text[: context.max_output_size]
                return ToolResult(
                    success=True,
                    data={"operation": operation, "path": str(rel_path), "data": data},
                )

            if operation == "write_file":
                if content is None:
                    return ToolResult(
                        success=False,
                        error_message="'content' is required for write_file",
                    )

                def _write() -> None:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(content, encoding="utf-8")

                await asyncio.to_thread(_write)
                return ToolResult(
                    success=True,
                    data={"operation": operation, "path": str(rel_path), "data": "ok"},
                    files_modified=[target],
                )

            if operation == "list_dir":
                if not target.exists() or not target.is_dir():
                    return ToolResult(
                        success=False, error_message="Directory does not exist"
                    )

                def _list() -> list[dict[str, Any]]:
                    entries: list[dict[str, Any]] = []
                    for p in target.iterdir():
                        entries.append(
                            {
                                "name": p.name,
                                "is_dir": p.is_dir(),
                                "size": p.stat().st_size if p.is_file() else None,
                            }
                        )
                    return entries

                entries = await asyncio.to_thread(_list)
                return ToolResult(
                    success=True,
                    data={
                        "operation": operation,
                        "path": str(rel_path),
                        "data": entries,
                    },
                )

            return ToolResult(
                success=False, error_message=f"Unsupported operation: {operation}"
            )
        except Exception as exc:  # pragma: no cover - safety net
            return ToolResult(success=False, error_message=str(exc))
