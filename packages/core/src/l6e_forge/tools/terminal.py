from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import asyncio
import shlex

from l6e_forge.tools.base import ITool
from l6e_forge.types.tool import ToolContext, ToolResult


@dataclass
class TerminalTool(ITool):
    name: str = "terminal"
    description: str = "Execute a shell command in a sandboxed, non-interactive way"
    category: str = "system"
    version: str = "0.1.0"

    def get_parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "cwd": {"type": "string"},
                "timeout": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 120,
                    "default": 30,
                },
            },
            "required": ["command"],
            "additionalProperties": False,
        }

    def get_return_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "returncode": {"type": "integer"},
                "stdout": {"type": "string"},
                "stderr": {"type": "string"},
            },
            "required": ["returncode"],
        }

    async def validate_parameters(self, parameters: dict[str, Any]) -> bool:
        cmd = parameters.get("command")
        return isinstance(cmd, str) and len(cmd.strip()) > 0

    async def initialize(self) -> None:  # pragma: no cover
        return None

    async def cleanup(self) -> None:  # pragma: no cover
        return None

    async def execute(
        self, parameters: dict[str, Any], context: ToolContext
    ) -> ToolResult:
        if not await self.validate_parameters(parameters):
            return ToolResult(success=False, error_message="Invalid parameters")

        # Simple safety: disallow interactive and background control characters
        command = parameters["command"].strip()
        if any(
            x in command
            for x in ["| less", "| more", "tail -f", "top", "htop", "vim", "nano"]
        ):
            return ToolResult(
                success=False, error_message="Interactive commands are not allowed"
            )

        timeout = int(parameters.get("timeout", 30))
        cwd_rel = parameters.get("cwd")
        cwd = (
            (context.workspace_path / cwd_rel).resolve()
            if cwd_rel
            else context.workspace_path.resolve()
        )

        if not str(cwd).startswith(str(context.workspace_path.resolve())):
            return ToolResult(
                success=False, error_message="cwd must be within workspace"
            )

        args = shlex.split(command)

        async def _run() -> tuple[int, str, str]:
            try:
                proc = await asyncio.create_subprocess_exec(
                    *args,
                    cwd=str(cwd),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                try:
                    out, err = await asyncio.wait_for(
                        proc.communicate(), timeout=timeout
                    )
                except asyncio.TimeoutError:
                    try:
                        proc.kill()
                    except Exception:
                        pass
                    return 124, "", "Command timed out"
                return (
                    proc.returncode or 0,
                    out.decode("utf-8", errors="replace"),
                    err.decode("utf-8", errors="replace"),
                )
            except FileNotFoundError:
                return 127, "", "Command not found"
            except Exception as exc:  # pragma: no cover
                return 1, "", str(exc)

        code, stdout, stderr = await _run()
        # Respect output size limits
        stdout = stdout[: context.max_output_size]
        stderr = stderr[: context.max_output_size]
        return ToolResult(
            success=code == 0,
            data={"returncode": code, "stdout": stdout, "stderr": stderr},
        )
