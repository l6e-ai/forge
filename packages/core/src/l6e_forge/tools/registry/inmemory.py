from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import uuid

from l6e_forge.types.core import AgentID, ToolID
from l6e_forge.types.tool import ToolContext, ToolResult, ToolSpec
from l6e_forge.tools.base import ITool
from l6e_forge.tools.registry.base import IToolRegistry


@dataclass
class _RegisteredTool:
    tool_id: ToolID
    tool: ITool
    spec: ToolSpec


class InMemoryToolRegistry(IToolRegistry):
    """Simple in-memory registry for tools.

    - Stores tool instances keyed by ToolID
    - Provides basic discovery and execution
    - Tracks per-agent tool mappings minimally
    """

    def __init__(self) -> None:
        self._tools: dict[ToolID, _RegisteredTool] = {}
        self._agent_to_tool_ids: dict[AgentID, list[ToolID]] = {}

    # Registration
    def register_tool(self, tool: ITool) -> ToolID:
        tool_id = uuid.uuid4()
        spec = ToolSpec(
            name=tool.name,
            description=tool.description,
            category=tool.category,
            version=getattr(tool, "version", "0.1.0"),
        )
        self._tools[tool_id] = _RegisteredTool(tool_id=tool_id, tool=tool, spec=spec)
        return tool_id

    def unregister_tool(self, tool_id: ToolID) -> None:
        self._tools.pop(tool_id, None)
        for tool_ids in self._agent_to_tool_ids.values():
            try:
                tool_ids.remove(tool_id)
            except ValueError:
                pass

    def get_tool(self, tool_id: ToolID) -> ITool:
        return self._tools[tool_id].tool

    # Discovery
    def list_tools(self, category: str | None = None) -> list[ToolSpec]:
        specs = [rt.spec for rt in self._tools.values()]
        if category:
            specs = [s for s in specs if s.category == category]
        return specs

    def search_tools(self, query: str) -> list[ToolSpec]:
        q = query.lower().strip()
        return [
            rt.spec
            for rt in self._tools.values()
            if q in rt.spec.name.lower() or q in rt.spec.description.lower()
        ]

    def get_tools_for_agent(self, agent_id: AgentID) -> list[ITool]:
        ids = self._agent_to_tool_ids.get(agent_id, [])
        return [self._tools[i].tool for i in ids if i in self._tools]

    def assign_tools_to_agent(self, agent_id: AgentID, tool_ids: list[ToolID]) -> None:
        self._agent_to_tool_ids[agent_id] = list(tool_ids)

    # Execution
    async def execute_tool(
        self, tool_id: ToolID, parameters: dict[str, Any], context: ToolContext
    ) -> ToolResult:
        tool = self.get_tool(tool_id)
        return await tool.execute(parameters, context)
