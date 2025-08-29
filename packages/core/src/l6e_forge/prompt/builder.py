from dataclasses import dataclass
from typing import Any, Iterable
from pathlib import Path

from jinja2 import Environment, StrictUndefined

from l6e_forge.types.core import AgentContext, Message
from .loader import PromptTemplateLoader


def _message_to_dict(m: Message) -> dict[str, Any]:
    return {
        "content": m.content,
        "role": m.role,
        "timestamp": m.timestamp.isoformat(),
        "message_id": str(m.message_id),
        "conversation_id": str(m.conversation_id),
        "metadata": m.metadata,
    }


@dataclass
class PromptBuilder:
    """Render prompts with Jinja2 using AgentContext and conversation history.

    - Provides `history_k(k)` to fetch last k messages via the attached history provider
    - Exposes `context` and `history` (already attached to AgentContext by runtime)
    - Ensures safe defaults with StrictUndefined to catch template mistakes
    """

    env: Environment
    loader: PromptTemplateLoader

    def __init__(self, search_paths: Iterable[str | Path] | None = None) -> None:
        self.env = Environment(
            autoescape=False,
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.loader = PromptTemplateLoader([Path(p) for p in (search_paths or [])])

    async def render(
        self,
        template_str: str,
        context: AgentContext,
        extra_vars: dict[str, Any] | None = None,
        k_limit: int | None = None,
    ) -> str:
        template = self.env.from_string(template_str)

        # Resolve history via provider if k_limit is set; otherwise use context.conversation_history
        history: list[Message] = context.conversation_history
        provider = getattr(context, "history_provider", None)
        if k_limit is not None and provider is not None:
            try:
                # Get last k messages
                full = await provider.get_recent(context.conversation_id, limit=k_limit)
                history = full[-k_limit:]
            except Exception:
                # Fallback to whatever is on context
                history = (
                    context.conversation_history[-k_limit:]
                    if context.conversation_history
                    else []
                )

        # Prepare vars for template
        vars: dict[str, Any] = {
            "context": context,
            "history": history,
            "history_dicts": [_message_to_dict(m) for m in history],
            # Convenience helpers
            "history_k": lambda k: (history[-k:] if k is not None else history),
        }
        if extra_vars:
            vars.update(extra_vars)

        return template.render(**vars)

    async def render_from_file(
        self,
        template_ref: str,
        context: AgentContext,
        extra_vars: dict[str, Any] | None = None,
        k_limit: int | None = None,
        workspace_root: str | Path | None = None,
        agent_name: str | None = None,
    ) -> str:
        # Default workspace root to context.workspace_path when not provided
        root_path = (
            Path(workspace_root).resolve()
            if workspace_root is not None
            else getattr(context, "workspace_path", Path.cwd())
        )
        tmpl = self.loader.load(template_ref, root_path, agent_name)
        return await self.render(tmpl, context, extra_vars=extra_vars, k_limit=k_limit)
