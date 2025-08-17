from __future__ import annotations

from agent_forge.cli.templates import (
    AGENT_ECHO_PY,
    AGENT_OLLAMA_PY,
    AGENT_ASSISTANT_BASIC_PY,
    AGENT_ASSISTANT_MODEL_PY,
    CONFIG_TOML,
)
from agent_forge.cli.templates.providers.ollama import OllamaProviderTemplate
from agent_forge.cli.templates.providers.lmstudio import LMStudioProviderTemplate
from agent_forge.types.workspace import TemplateFile, TemplateSpec


def build_echo_spec() -> TemplateSpec:
    return TemplateSpec(
        name="basic",
        description="Basic echo agent",
        files=[
            TemplateFile(path="agent.py", content=AGENT_ECHO_PY, file_type="python"),
            TemplateFile(path="config.toml", content=CONFIG_TOML, file_type="toml"),
        ],
        variables={},
        author="agent-forge",
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
        author="agent-forge",
        tags=["assistant", "ollama"],
    )


def get_template_spec(template: str, provider: str) -> TemplateSpec:
    template = template.lower()
    provider = provider.lower()
    if template in ("basic", "echo"):
        return build_echo_spec()
    if template in ("assistant", "assistant-basic"):
        if provider in ("", "none", "local"):
            return TemplateSpec(
                name="assistant-basic",
                description="Basic assistant agent",
                files=[
                    TemplateFile(path="agent.py", content=AGENT_ASSISTANT_BASIC_PY, file_type="python"),
                    TemplateFile(path="config.toml", content=CONFIG_TOML, file_type="toml"),
                ],
                variables={},
                author="agent-forge",
                tags=["assistant", "basic"],
            )
        # Provider plug-in registry
        provider_vars: dict[str, str]
        if provider == "ollama":
            provider_vars = OllamaProviderTemplate().get_template_vars(model="{{ model }}", endpoint=None)
        elif provider == "lmstudio":
            provider_vars = LMStudioProviderTemplate().get_template_vars(model="{{ model }}", endpoint=None)
        else:
            # Future: LM Studio, OpenAI, etc.
            raise ValueError(f"Provider '{provider}' not supported for template '{template}'.")

        # Compose a provider-flexible assistant template
        content = (
            AGENT_ASSISTANT_MODEL_PY.replace("{{ model_imports }}", provider_vars["model_imports"])  # type: ignore[index]
            .replace("{{ model_usage }}", provider_vars["model_usage"])  # type: ignore[index]
        )
        return TemplateSpec(
            name=f"assistant-{provider}",
            description=f"Assistant using {provider}",
            files=[
                TemplateFile(path="agent.py", content=content, file_type="python"),
                TemplateFile(path="config.toml", content=CONFIG_TOML, file_type="toml"),
            ],
            variables={},
            author="agent-forge",
            tags=["assistant", provider],
        )
        # Future: add other providers here
        raise ValueError(f"Provider '{provider}' not supported for template '{template}'.")
    # Direct provider-qualified names
    if template in ("assistant-ollama",):
        return build_ollama_spec()
    raise ValueError(f"Unknown template '{template}'.")


