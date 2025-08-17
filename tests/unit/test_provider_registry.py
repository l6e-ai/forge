from __future__ import annotations

from pathlib import Path

from agent_forge.models.providers.registry import load_endpoints_from_config, get_manager


def test_load_endpoints_from_config(tmp_path: Path) -> None:
    cfg = tmp_path / "forge.toml"
    cfg.write_text(
        """
[models]
default_provider = "ollama"

[models.endpoints]
ollama = "http://localhost:11434"
lmstudio = "http://localhost:1234/v1"
""".strip(),
        encoding="utf-8",
    )

    default, eps = load_endpoints_from_config(tmp_path)
    assert default == "ollama"
    assert eps["ollama"].endswith(":11434")
    assert eps["lmstudio"].endswith("/v1")


def test_get_manager_ollama_and_lmstudio() -> None:
    eps = {"ollama": "http://localhost:11434", "lmstudio": "http://localhost:1234/v1"}
    m1 = get_manager("ollama", eps)
    m2 = get_manager("lmstudio", eps)
    # Smoke: they are different types and have required methods
    assert hasattr(m1, "chat") and hasattr(m2, "chat")


