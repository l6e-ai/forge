from typing import Any, Protocol

from l6e_forge.types.workspace import (
    TemplateSpec,
    TemplateContext,
    TemplateGenerationResult,
)


class IWorkspaceTemplateEngine(Protocol):
    """Template engine interface"""

    async def render_template(
        self, template_content: str, variables: dict[str, Any]
    ) -> str:
        """Render a template with variables"""
        ...

    async def generate_from_template(
        self, template_spec: TemplateSpec, context: TemplateContext
    ) -> TemplateGenerationResult:
        """Generate files from a template"""
        ...

    def list_templates(self) -> list[TemplateSpec]:
        """List available templates"""
        ...

    def get_template(self, template_name: str) -> TemplateSpec:
        """Get a specific template"""
        ...
