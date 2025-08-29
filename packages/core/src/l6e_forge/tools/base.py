from typing import Any, Protocol

from l6e_forge.types.tool import ToolContext, ToolResult


class ITool(Protocol):
    """Tool interface protocol"""

    # Tool identity
    name: str
    description: str
    category: str
    version: str

    # Tool specification
    def get_parameters_schema(self) -> dict[str, Any]:
        """Get JSON Schema for tool parameters"""
        ...

    def get_return_schema(self) -> dict[str, Any]:
        """Get JSON Schema for tool return value"""
        ...

    # Tool execution
    async def execute(
        self, parameters: dict[str, Any], context: ToolContext
    ) -> ToolResult:
        """Execute the tool with given parameters"""
        ...

    async def validate_parameters(self, parameters: dict[str, Any]) -> bool:
        """Validate tool parameters"""
        ...

    # Tool lifecycle
    async def initialize(self) -> None:
        """Initialize the tool"""
        ...

    async def cleanup(self) -> None:
        """Clean up tool resources"""
        ...
