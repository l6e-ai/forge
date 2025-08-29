from dataclasses import dataclass, field
from typing import Dict, List

from l6e_forge.workspace.template_engine.jinja import JinjaTemplateEngine


# TODO update w/ depends on and health checks for services


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
    restart: unless-stopped
            """
        ).strip("\n"),
        "redis": (
            """
  redis:
    image: redis:{{ tag | default('alpine') }}
    ports:
      - "{{ port | default('6379') }}:{{ port | default('6379') }}"
    restart: unless-stopped
            """
        ).strip("\n"),
        "ollama": (
            """
  ollama:
    image: ollama/ollama:{{ tag | default('latest') }}
    ports:
      - "{{ port | default('11434') }}:{{ port | default('11434') }}"
    restart: unless-stopped
            """
        ).strip("\n"),
        "monitor": (
            """
  monitor:
    image: l6eai/l6e-forge-monitor:{{ tag | default('latest') }}
    ports:
      - "{{ port | default('8321') }}:{{ port | default('8321') }}"
    restart: unless-stopped
            """
        ).strip("\n"),
        "api": (
            """
  api:
    image: l6eai/l6e-forge-api:{{ tag | default('latest') }}
    environment:
      - AF_MONITOR_URL=http://monitor:8321
      - AF_WORKSPACE=/workspace
      - OLLAMA_HOST=http://host.docker.internal:11434
      - LMSTUDIO_HOST=http://host.docker.internal:1234/v1
      - AF_MEMORY_PROVIDER={{ memory_provider | default('memory') }}
      - QDRANT_URL=http://qdrant:6333
      - AF_DB_URL={{ db_url | default('postgresql://forge:forge@postgres:5432/forge') }}
    volumes:
      - ./:/workspace
    ports:
      - "{{ port | default('8000') }}:{{ port | default('8000') }}"
    restart: unless-stopped
            """
        ).strip("\n"),
        "ui": (
            """
  ui:
    image: l6eai/l6e-forge-ui:{{ tag | default('latest') }}
    # We must tunnel through localhost since we are running in our browser
    # (instead of using api/monitor service names in docker network)
    environment:
      - VITE_API_BASE={{ api_base | default('http://localhost:8000/api') }}
    {% if ui_mount is defined and ui_mount %}
    volumes:
      - "{{ ui_mount }}:/app/static/ui:ro"
    {% endif %}
    ports:
      - "{{ port | default('8173') }}:{{ port | default('8173') }}"
    restart: unless-stopped
            """
        ).strip("\n"),
        "postgres": (
            """
  postgres:
    image: postgres:{{ tag | default('17-alpine') }}
    environment:
      - POSTGRES_USER={{ user | default('forge') }}
      - POSTGRES_PASSWORD={{ password | default('forge') }}
      - POSTGRES_DB={{ database | default('forge') }}
    ports:
      - "{{ port | default('5432') }}:5432"
    volumes:
      - ./migrations:/docker-entrypoint-initdb.d:ro
    restart: unless-stopped
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

    def _parse_services_block_bounds(self, text: str) -> tuple[int | None, int]:
        """Find the start and end line indexes (exclusive end) of the top-level services block.

        Returns a tuple (start_index, end_index). If services is not found at the
        top level, start_index will be None and end_index will be len(lines).
        """
        lines = text.splitlines()
        services_start: int | None = None
        for idx, line in enumerate(lines):
            # Top-level 'services:' line has no leading indentation
            if line.strip() == "services:" and (len(line) == len(line.lstrip())):
                services_start = idx
                break
        if services_start is None:
            return None, len(lines)
        # Find next top-level key after services
        for j in range(services_start + 1, len(lines)):
            lj = lines[j]
            if not lj.strip():
                continue
            if len(lj) == len(lj.lstrip()) and not lj.startswith("#"):
                # Found next top-level key
                return services_start, j
        return services_start, len(lines)

    def _existing_service_names(self, text: str) -> set[str]:
        """Parse existing service names from a compose text without YAML deps.

        Looks for lines with two-space indentation directly under the top-level
        services block, shaped like '  name:'.
        """
        names: set[str] = set()
        start, end = self._parse_services_block_bounds(text)
        if start is None:
            return names
        lines = text.splitlines()
        for k in range(start + 1, end):
            line = lines[k]
            if line.startswith("  ") and (not line.startswith("    ")):
                stripped = line.strip()
                if stripped.endswith(":") and " " not in stripped[:-1]:
                    # Capture token before ':'
                    names.add(stripped[:-1])
        return names

    async def merge(
        self, existing_text: str, services: List[ComposeServiceSpec]
    ) -> str:
        """Merge missing services into an existing docker-compose text.

        - If a top-level services block exists, append only the missing services
          into that block.
        - If it does not, return the existing text unchanged.
        """
        existing_names = self._existing_service_names(existing_text)
        # Determine which specs are missing
        missing_specs: List[ComposeServiceSpec] = [
            s for s in services if s.name not in existing_names
        ]
        if not missing_specs:
            return existing_text

        # Render missing fragments
        rendered_fragments: List[str] = []
        for spec in missing_specs:
            tmpl = self._templates.get(spec.name)
            if not tmpl:
                continue
            rendered = await self._engine.render_template(tmpl, spec.context)
            rendered_fragments.append(rendered.strip("\n"))
        if not rendered_fragments:
            return existing_text

        start, end = self._parse_services_block_bounds(existing_text)
        if start is None:
            # Cannot safely merge without a services block; return existing as-is
            return existing_text

        insertion = (
            ("\n" if not existing_text.endswith("\n") else "")
            + "\n".join(rendered_fragments)
            + "\n"
        )
        lines = existing_text.splitlines()
        # Insert fragments right before end of services block (or EOF)
        new_lines = lines[:end] + insertion.splitlines() + lines[end:]
        return "\n".join(new_lines) + ("\n" if not existing_text.endswith("\n") else "")


__all__ = ["ComposeTemplateService", "ComposeServiceSpec"]
