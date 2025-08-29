from __future__ import annotations

from pathlib import Path
from typer.testing import CliRunner

from l6e_forge.models.auto import (
    ensure_ollama_models,
)
from l6e_forge_cli.main import app as main_app


def test_ensure_ollama_models_pulls_and_adjusts_when_none_available(
    monkeypatch,
) -> None:
    # Simulate an empty Ollama registry initially, then models appear after pulls
    current: set[str] = set()

    def fake_list(_endpoint: str = "http://localhost:11434") -> list[str]:
        return sorted(current)

    pulled: list[str] = []

    def fake_pull(name: str) -> None:
        pulled.append(name)
        # When a model is "pulled", add it to the available set
        current.add(name)

    monkeypatch.setattr("l6e_forge.models.auto._ollama_list_models", fake_list)
    monkeypatch.setattr("l6e_forge.models.auto._maybe_pull_model", fake_pull)

    # Request a tag that likely needs alias adjustment (":8b-instruct" -> ":8b")
    recs = {"chat": "llama3.1:8b-instruct", "embedding": "nomic-embed-text:latest"}
    resolved = ensure_ollama_models(recs)

    # Should have attempted to pull at least one tag
    assert pulled, "bootstrap should attempt to pull when none available"
    # Resolved chat should fall back to an existing alias if needed
    assert resolved["chat"] in current
    assert resolved["embedding"] in current


def test_cli_bootstrap_updates_config_when_no_models(
    tmp_path: Path, monkeypatch
) -> None:
    # Prepare a minimal agent with config
    agent_dir = tmp_path / "agent"
    agent_dir.mkdir(parents=True)
    (agent_dir / "agent.py").write_text("print('agent')\n", encoding="utf-8")
    (agent_dir / "config.toml").write_text(
        """
[agent]
name = "demo"

[model.auto]
enabled = true
providers = ["ollama"]
""".strip()
        + "\n",
        encoding="utf-8",
    )

    # Fake Ollama env: nothing available at first, models appear after pull
    current: set[str] = set()

    def fake_list(_endpoint: str = "http://localhost:11434") -> list[str]:
        return sorted(current)

    def fake_pull(name: str) -> None:
        current.add(name)

    monkeypatch.setattr("l6e_forge.models.auto._ollama_list_models", fake_list)
    monkeypatch.setattr("l6e_forge.models.auto._maybe_pull_model", fake_pull)

    # Run CLI bootstrap
    runner = CliRunner()
    result = runner.invoke(
        main_app, ["models", "bootstrap", str(agent_dir)], catch_exceptions=False
    )
    assert result.exit_code == 0, result.output

    # Config should now have model/memory entries
    cfg = (agent_dir / "config.toml").read_text(encoding="utf-8")
    assert "[model]" in cfg
    assert 'provider = "ollama"' in cfg
    assert 'model = "' in cfg
    assert "[memory]" in cfg
    assert 'embedding_model = "' in cfg
