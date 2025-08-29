from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from jinja2 import Environment, StrictUndefined

from l6e_forge.workspace.template_engine.base import IWorkspaceTemplateEngine
from l6e_forge.types.workspace import (
    TemplateContext,
    TemplateGenerationResult,
    TemplateSpec,
)


@dataclass
class JinjaTemplateEngine(IWorkspaceTemplateEngine):
    env: Environment

    def __init__(self) -> None:
        self.env = Environment(autoescape=False, undefined=StrictUndefined)

    async def render_template(
        self, template_content: str, variables: dict[str, Any]
    ) -> str:
        template = self.env.from_string(template_content)
        return template.render(**variables)

    async def generate_from_template(
        self, template_spec: TemplateSpec, context: TemplateContext
    ) -> TemplateGenerationResult:
        result = TemplateGenerationResult(
            success=True,
            template_name=template_spec.name,
            target_path=context.target_path,
        )
        for tf in template_spec.files:
            # Simple include-all for MVP
            rendered = await self.render_template(tf.content, context.variable_values)
            out_path = context.target_path / tf.path
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(rendered, encoding=tf.encoding)
            result.files_created.append(out_path)
        return result

    def list_templates(self) -> list[TemplateSpec]:  # noqa: D401
        return []

    def get_template(self, template_name: str) -> TemplateSpec:  # noqa: D401
        raise NotImplementedError
