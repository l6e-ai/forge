from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from agent_forge.cli.main import app as main_app


def _write_min_agent(dir_path: Path, name: str = "demo") -> Path:
    agent_dir = dir_path / name
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "agent.py").write_text(
        (
            """
from agent_forge.types.core import AgentContext, AgentResponse, Message

class Agent:
    name = "{name}"
    async def handle_message(self, message: Message, context: AgentContext) -> AgentResponse:
        return AgentResponse(content="ok", agent_id=self.name, response_time=0.0)
"""
        ).strip().format(name=name),
        encoding="utf-8",
    )
    return agent_dir


def test_pkg_build_and_inspect(tmp_path: Path) -> None:
    runner = CliRunner()
    agent_dir = _write_min_agent(tmp_path, name="demo")
    dist_dir = tmp_path / "dist"

    # Build package
    result_build = runner.invoke(
        main_app,
        [
            "pkg",
            "build",
            str(agent_dir),
            "--out",
            str(dist_dir),
            "--version",
            "0.2.0",
            "--description",
            "Demo agent",
        ],
        catch_exceptions=False,
    )
    assert result_build.exit_code == 0, result_build.output
    pkg_path = dist_dir / "demo-0.2.0.l6e"
    assert pkg_path.exists()

    # Inspect
    result_inspect = runner.invoke(main_app, ["pkg", "inspect", str(pkg_path)], catch_exceptions=False)
    assert result_inspect.exit_code == 0, result_inspect.output
    out = result_inspect.output
    assert "name: demo" in out.lower()
    assert "version: 0.2.0" in out.lower()
    assert "description: demo agent" in out.lower()

    # Ensure manifest contains embedded agent_config when a config.toml is present
    (agent_dir / "config.toml").write_text(
        (
            """
[agent]
description = "Config Desc"
[model]
provider = "ollama"
model = "llama3.2:3b"
"""
        ).strip(),
        encoding="utf-8",
    )
    # rebuild
    result_build2 = runner.invoke(
        main_app,
        [
            "pkg",
            "build",
            str(agent_dir),
            "--out",
            str(dist_dir),
            "--version",
            "0.2.1",
        ],
        catch_exceptions=False,
    )
    assert result_build2.exit_code == 0, result_build2.output
    pkg_path2 = dist_dir / "demo-0.2.1.l6e"
    assert pkg_path2.exists()

    # Open the manifest and check for agent_config fields
    import zipfile, io as _io, tomllib as _tomllib

    with zipfile.ZipFile(pkg_path2, "r") as zf:
        with zf.open("package.toml") as f:
            data = _tomllib.load(_io.BytesIO(f.read()))
    assert "agent_config" in data
    assert data["agent_config"]["agent"]["description"] == "Config Desc"
    assert data["agent_config"]["model"]["provider"] == "ollama"

    # Use CLI --show-config to display the embedded config
    result_show_cfg = runner.invoke(main_app, ["pkg", "inspect", str(pkg_path2), "--show-config"], catch_exceptions=False)
    assert result_show_cfg.exit_code == 0, result_show_cfg.output
    out_cfg = result_show_cfg.output
    assert "[agent_config]" in out_cfg
    assert "description = \"Config Desc\"" in out_cfg
    assert "provider = \"ollama\"" in out_cfg


def test_pkg_install_into_workspace_and_overwrite(tmp_path: Path) -> None:
    runner = CliRunner()
    # Build a package first
    agent_dir = _write_min_agent(tmp_path / "src", name="demo")
    dist_dir = tmp_path / "dist"
    result_build = runner.invoke(
        main_app,
        ["pkg", "build", str(agent_dir), "--out", str(dist_dir), "--version", "1.0.0"],
        catch_exceptions=False,
    )
    assert result_build.exit_code == 0, result_build.output
    pkg_path = dist_dir / "demo-1.0.0.l6e"
    assert pkg_path.exists()

    # Prepare a workspace
    ws_path = tmp_path / "ws"
    result_init = runner.invoke(main_app, ["init", str(ws_path)], catch_exceptions=False)
    assert result_init.exit_code == 0, result_init.output

    # Install into workspace
    result_install = runner.invoke(
        main_app,
        ["pkg", "install", str(pkg_path), "--workspace", str(ws_path)],
        catch_exceptions=False,
    )
    assert result_install.exit_code == 0, result_install.output
    installed_agent = ws_path / "agents" / "demo" / "agent.py"
    assert installed_agent.exists()

    # Reinstall without overwrite should fail
    result_install_no_over = runner.invoke(
        main_app,
        ["pkg", "install", str(pkg_path), "--workspace", str(ws_path)],
        catch_exceptions=False,
    )
    assert result_install_no_over.exit_code != 0
    assert "already exists" in result_install_no_over.output.lower()

    # Change the source package's agent.py to detect overwrite
    (agent_dir / "agent.py").write_text("print('new')\n", encoding="utf-8")
    result_build2 = runner.invoke(
        main_app,
        ["pkg", "build", str(agent_dir), "--out", str(dist_dir), "--version", "1.0.1"],
        catch_exceptions=False,
    )
    assert result_build2.exit_code == 0, result_build2.output
    pkg_path2 = dist_dir / "demo-1.0.1.l6e"
    assert pkg_path2.exists()

    # Overwrite install
    result_install_over = runner.invoke(
        main_app,
        ["pkg", "install", str(pkg_path2), "--workspace", str(ws_path), "--overwrite"],
        catch_exceptions=False,
    )
    assert result_install_over.exit_code == 0, result_install_over.output
    assert installed_agent.read_text(encoding="utf-8").strip() == "print('new')"


def test_pkg_build_requires_agent_py(tmp_path: Path) -> None:
    runner = CliRunner()
    empty_dir = tmp_path / "empty_agent"
    empty_dir.mkdir(parents=True)
    result = runner.invoke(main_app, ["pkg", "build", str(empty_dir)], catch_exceptions=False)
    assert result.exit_code != 0
    assert "agent.py not found" in result.output.lower()


def test_pkg_install_requires_workspace(tmp_path: Path) -> None:
    runner = CliRunner()
    # Make a valid package
    agent_dir = _write_min_agent(tmp_path / "src", name="demo")
    dist_dir = tmp_path / "dist"
    result_build = runner.invoke(
        main_app,
        ["pkg", "build", str(agent_dir), "--out", str(dist_dir)],
        catch_exceptions=False,
    )
    assert result_build.exit_code == 0
    pkg_path = dist_dir / "demo-0.1.0.l6e"
    assert pkg_path.exists()

    # Try to install into a non-workspace
    no_ws = tmp_path / "noworkspace"
    no_ws.mkdir(parents=True)
    result_install = runner.invoke(
        main_app,
        ["pkg", "install", str(pkg_path), "--workspace", str(no_ws)],
        catch_exceptions=False,
    )
    assert result_install.exit_code != 0
    assert "not a workspace" in result_install.output.lower() or "missing" in result_install.output.lower()


