from __future__ import annotations

from typing import Protocol

from l6e_forge.types.core import AgentResponse, AgentContext


class IResultProcessor(Protocol):
    async def process(
        self, response: AgentResponse, context: AgentContext
    ) -> AgentResponse: ...


class DefaultResultProcessor:
    async def process(
        self, response: AgentResponse, context: AgentContext
    ) -> AgentResponse:
        return response


_DEFAULT_PROCESSOR = DefaultResultProcessor()


def get_default_processor() -> IResultProcessor:
    return _DEFAULT_PROCESSOR
