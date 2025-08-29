from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import json

from l6e_forge.tools.base import ITool
from l6e_forge.types.tool import ToolContext, ToolResult


@dataclass
class CodeUtilsTool(ITool):
    name: str = "code.utils"
    description: str = (
        "Utilities for working with code snippets and JSON (format, validate)"
    )
    category: str = "utility"
    version: str = "0.1.0"

    def get_parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["json_validate", "json_format"],
                },
                "text": {"type": "string"},
            },
            "required": ["operation", "text"],
            "additionalProperties": False,
        }

    def get_return_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string"},
                "valid": {"type": "boolean"},
                "text": {"type": "string"},
                "error": {"type": "string"},
            },
            "required": ["operation"],
        }

    async def validate_parameters(self, parameters: dict[str, Any]) -> bool:
        op = parameters.get("operation")
        text = parameters.get("text")
        return op in {"json_validate", "json_format"} and isinstance(text, str)

    async def initialize(self) -> None:  # pragma: no cover
        return None

    async def cleanup(self) -> None:  # pragma: no cover
        return None

    async def execute(
        self, parameters: dict[str, Any], context: ToolContext
    ) -> ToolResult:
        if not await self.validate_parameters(parameters):
            return ToolResult(success=False, error_message="Invalid parameters")
        op: str = parameters["operation"]
        text: str = parameters["text"]

        try:
            if op == "json_validate":
                try:
                    _ = json.loads(text)
                    return ToolResult(
                        success=True, data={"operation": op, "valid": True}
                    )
                except json.JSONDecodeError as exc:
                    return ToolResult(
                        success=True,
                        data={"operation": op, "valid": False, "error": str(exc)},
                    )

            if op == "json_format":
                obj = json.loads(text)
                pretty = json.dumps(obj, indent=2, ensure_ascii=False)
                return ToolResult(success=True, data={"operation": op, "text": pretty})

            return ToolResult(
                success=False, error_message=f"Unsupported operation: {op}"
            )
        except Exception as exc:  # pragma: no cover
            return ToolResult(success=False, error_message=str(exc))
