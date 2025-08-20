from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from agent_forge.workspace.template_engine.jinja import JinjaTemplateEngine


@dataclass
class ComposeServiceSpec:
    name: str
    context: dict = field(default_factory=dict)


class ComposeTemplateService:
    """Generate docker-compose YAML from service templates.

    This is a simple Jinja-backed generator that can be evolved with more
    parameters without changing callers.
    """

    # Minimal inline templates; can be moved to external files later
    _templates: Dict[str, str] = {
        "qdrant": (
            """
  qdrant:
    image: qdrant/qdrant:{{ tag | default('latest') }}
    ports:
      - "{{ port | default('6333') }}:{{ port | default('6333') }}"
            """
        ).strip("\n"),
        "redis": (
            """
  redis:
    image: redis:{{ tag | default('alpine') }}
    ports:
      - "{{ port | default('6379') }}:{{ port | default('6379') }}"
            """
        ).strip("\n"),
        "ollama": (
            """
  ollama:
    image: ollama/ollama:{{ tag | default('latest') }}
    ports:
      - "{{ port | default('11434') }}:{{ port | default('11434') }}"
            """
        ).strip("\n"),
        "monitor": (
            """
  monitor:
    image: agent-forge/monitor:{{ tag | default('latest') }}
    ports:
      - "{{ port | default('8321') }}:{{ port | default('8321') }}"
            """
        ).strip("\n"),
    }

    def __init__(self) -> None:
        self._engine = JinjaTemplateEngine()

    async def generate(self, services: List[ComposeServiceSpec]) -> str:
        """Render a compose file from service specs."""
        header = "version: '3.8'\nservices:\n"
        fragments: List[str] = []
        for spec in services:
            tmpl = self._templates.get(spec.name)
            if not tmpl:
                continue
            rendered = await self._engine.render_template(tmpl, spec.context)
            fragments.append(rendered.strip("\n"))
        body = "\n".join(fragments)
        return header + body + "\n"


__all__ = ["ComposeTemplateService", "ComposeServiceSpec"]


