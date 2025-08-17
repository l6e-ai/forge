from __future__ import annotations

from pathlib import Path

import pytest

from agent_forge.workspace.manager.local import LocalWorkspaceManager


@pytest.mark.asyncio
async def test_create_and_validate_workspace(tmp_path: Path) -> None:
    manager = LocalWorkspaceManager()
    ws_path = tmp_path / "my-ws"

    await manager.create_workspace(ws_path)

    # Structure exists
    assert (ws_path / "forge.toml").exists()
    assert (ws_path / "agents").is_dir()
    assert (ws_path / ".forge" / "logs").is_dir()
    assert (ws_path / ".forge" / "data").is_dir()

    validation = await manager.validate_workspace(ws_path)
    assert validation.is_valid
    assert validation.config_valid
    assert validation.agents_valid


@pytest.mark.asyncio
async def test_load_workspace_state_counts_agents(tmp_path: Path) -> None:
    manager = LocalWorkspaceManager()
    ws_path = tmp_path / "my-ws"
    await manager.create_workspace(ws_path)

    # Initially empty
    state = await manager.load_workspace(ws_path)
    assert state.agent_count == 0
    assert state.active_agents == []

    # Add an agent folder
    agent_dir = ws_path / "agents" / "demo"
    agent_dir.mkdir(parents=True)
    (agent_dir / "agent.py").write_text("pass", encoding="utf-8")

    state2 = await manager.load_workspace(ws_path)
    assert state2.agent_count == 1
    assert "demo" in state2.active_agents


@pytest.mark.asyncio
async def test_validate_nonexistent_path(tmp_path: Path) -> None:
    manager = LocalWorkspaceManager()
    missing = tmp_path / "does-not-exist"

    result = await manager.validate_workspace(missing)
    assert not result.is_valid
    assert any("does not exist" in e for e in result.errors)


@pytest.mark.asyncio
async def test_validate_missing_config_and_dirs(tmp_path: Path) -> None:
    manager = LocalWorkspaceManager()
    # Create only the root directory without workspace files/dirs
    ws_path = tmp_path / "plain"
    ws_path.mkdir(parents=True)

    result = await manager.validate_workspace(ws_path)
    assert result.is_valid  # structure considered valid, but with warnings
    # Should warn about missing configs/dirs
    warnings = "\n".join(result.warnings)
    assert "forge.toml" in warnings
    assert "agents/" in warnings
    assert ".forge/" in warnings


@pytest.mark.asyncio
async def test_list_workspaces_detection(tmp_path: Path, monkeypatch) -> None:
    manager = LocalWorkspaceManager()

    # Case 1: Not a workspace
    def _fake_cwd1() -> Path:
        return tmp_path

    from pathlib import Path as _Path

    monkeypatch.setattr(_Path, "cwd", staticmethod(_fake_cwd1))
    assert manager.list_workspaces() == []

    # Case 2: Looks like a workspace
    (tmp_path / "agents").mkdir()
    (tmp_path / "forge.toml").write_text("[workspace]\nname='x'\n", encoding="utf-8")

    assert manager.list_workspaces() == [tmp_path.resolve()]


@pytest.mark.asyncio
async def test_load_workspace_status_error_when_path_missing(tmp_path: Path) -> None:
    manager = LocalWorkspaceManager()
    missing = tmp_path / "missing"
    state = await manager.load_workspace(missing)
    assert state.status == "error"
    assert state.agent_count == 0


