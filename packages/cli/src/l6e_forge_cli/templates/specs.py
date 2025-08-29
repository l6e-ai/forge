from __future__ import annotations

from l6e_forge_cli.templates import (
    AGENT_ECHO_PY,
    AGENT_OLLAMA_PY,
    AGENT_ASSISTANT_MODEL_PY,
    CONFIG_TOML,
)
from l6e_forge.types.workspace import TemplateFile, TemplateSpec


def build_echo_spec() -> TemplateSpec:
    return TemplateSpec(
        name="basic",
        description="Basic echo agent",
        files=[
            TemplateFile(path="agent.py", content=AGENT_ECHO_PY, file_type="python"),
            TemplateFile(path="config.toml", content=CONFIG_TOML, file_type="toml"),
        ],
        variables={},
        author="l6e-forge",
        tags=["echo", "basic"],
    )


def build_ollama_spec() -> TemplateSpec:
    return TemplateSpec(
        name="assistant-ollama",
        description="Assistant agent powered by Ollama",
        files=[
            TemplateFile(path="agent.py", content=AGENT_OLLAMA_PY, file_type="python"),
            TemplateFile(path="config.toml", content=CONFIG_TOML, file_type="toml"),
        ],
        variables={},
        author="l6e-forge",
        tags=["assistant", "ollama"],
    )


def get_template_spec(template: str, provider: str) -> TemplateSpec:
    template = template.lower()
    provider = provider.lower()
    if template in ("basic", "echo"):
        return build_echo_spec()
    if template in ("assistant", "assistant-basic"):
        # Default assistant now uses auto-bootstrap pattern and runtime manager
        return TemplateSpec(
            name="assistant-auto",
            description="Assistant agent using auto-bootstrap models",
            files=[
                TemplateFile(
                    path="agent.py",
                    content=AGENT_ASSISTANT_MODEL_PY,
                    file_type="python",
                ),
                TemplateFile(path="config.toml", content=CONFIG_TOML, file_type="toml"),
            ],
            variables={},
            author="l6e-forge",
            tags=["assistant", "auto"],
        )
    # Direct provider-qualified names
    if template in ("assistant-ollama",):
        return build_ollama_spec()
    raise ValueError(f"Unknown template '{template}'.")
