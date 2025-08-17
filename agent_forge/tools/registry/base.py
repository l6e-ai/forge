from typing import Any, Protocol

from agent_forge.types.tool import ToolContext, ToolResult, ToolSpec
from agent_forge.tools.base import ITool
from agent_forge.types.core import AgentID, ToolID

class IToolRegistry(Protocol):
    """Tool registry interface protocol"""
    
    # Tool registration
    def register_tool(self, tool: ITool) -> ToolID:
        """Register a new tool"""
        ...
    
    def unregister_tool(self, tool_id: ToolID) -> None:
        """Unregister a tool"""
        ...
    
    def get_tool(self, tool_id: ToolID) -> ITool:
        """Get a tool by ID"""
        ...
    
    # Tool discovery
    def list_tools(self, category: str | None = None) -> list[ToolSpec]:
        """List available tools, optionally filtered by category"""
        ...
    
    def search_tools(self, query: str) -> list[ToolSpec]:
        """Search for tools by query"""
        ...
    
    def get_tools_for_agent(self, agent_id: AgentID) -> list[ITool]:
        """Get tools available for a specific agent"""
        ...

    # Tool execution
    async def execute_tool(self, tool_id: ToolID, parameters: dict[str, Any], context: ToolContext) -> ToolResult:
        """Execute a tool"""
        ...
