from __future__ import annotations

from l6e_forge.types.core import AgentResponse, Message, AgentContext


class Agent:
    name: str = "demo"
    description: str = "Demo echo agent"
    version: str = "0.0.1"

    async def handle_message(self, message: Message, context: AgentContext) -> AgentResponse:  # noqa: D401
        import time

        start = time.perf_counter()
        reply = f"Echo: {message.content}"
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        # Use agent name as identifier for simple demos
        return AgentResponse(content=reply, agent_id=self.name, response_time=elapsed_ms)


