from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from l6e_forge.workspace.template_engine.jinja import JinjaTemplateEngine


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
    volumes:
      - ./data/qdrant:/qdrant/storage
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
    image: l6e-forge/monitor:{{ tag | default('latest') }}
    ports:
      - "{{ port | default('8321') }}:{{ port | default('8321') }}"
            """
        ).strip("\n"),
        "api": (
            """
  api:
    image: l6e-forge/api:{{ tag | default('latest') }}
    environment:
      - AF_MONITOR_URL=http://monitor:8321
      - AF_WORKSPACE=/workspace
      - OLLAMA_HOST=http://host.docker.internal:11434
      - LMSTUDIO_HOST=http://host.docker.internal:1234/v1
      - AF_MEMORY_PROVIDER={{ memory_provider | default('memory') }}
      - QDRANT_URL=http://qdrant:6333
      - AF_MEMORY_COLLECTION=agent_memory
    ports:
      - "{{ port | default('8000') }}:{{ port | default('8000') }}"
            """
        ).strip("\n"),
        "ui": (
            """
  ui:
    image: node:22-alpine
    working_dir: /app/site/agent-ui
    command: sh -c "npm ci && npm run dev -- --host 0.0.0.0"
    ports:
      - "{{ port | default('5173') }}:{{ port | default('5173') }}"
            """
        ).strip("\n"),
    }

    def __init__(self) -> None:
        self._engine = JinjaTemplateEngine()

    async def generate(self, services: List[ComposeServiceSpec]) -> str:
        """Render a compose file from service specs."""
        header = "services:\n"
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


