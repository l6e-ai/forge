from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from l6e_forge_cli.main import app as main_app
from l6e_forge.runtime.local import LocalRuntime
from l6e_forge.types.core import Message


def test_cli_init_and_list(tmp_path: Path) -> None:
    runner = CliRunner()
    ws_path = tmp_path / "ws"

    result_init = runner.invoke(main_app, ["init", str(ws_path)])
    assert result_init.exit_code == 0, result_init.output
    assert (ws_path / "forge.toml").exists()

    # list from the new workspace
    result_list = runner.invoke(main_app, ["list"], env={"PWD": str(ws_path)})
    # Typer's CliRunner does not change cwd; simulate by running via chdir context
    assert result_list.exit_code == 0, result_list.output


def test_cli_create_agent_and_list(tmp_path: Path, monkeypatch) -> None:
    runner = CliRunner()
    ws_path = tmp_path / "ws"

    # init workspace
    result_init = runner.invoke(main_app, ["init", str(ws_path)])
    assert result_init.exit_code == 0, result_init.output

    # create agent
    result_create = runner.invoke(
        main_app, ["create", "agent", "demo", "--workspace", str(ws_path)]
    )
    assert result_create.exit_code == 0, result_create.output
    assert (ws_path / "agents" / "demo" / "agent.py").exists()

    # list should show agent when run in ws cwd
    def _fake_cwd() -> Path:
        return ws_path

    from pathlib import Path as _Path

    monkeypatch.setattr(_Path, "cwd", staticmethod(_fake_cwd))
    result_list = runner.invoke(main_app, ["list"])
    assert result_list.exit_code == 0, result_list.output
    assert "demo" in result_list.output


def test_cli_create_duplicate_agent_fails(tmp_path: Path) -> None:
    runner = CliRunner()
    ws_path = tmp_path / "ws"
    result_init = runner.invoke(main_app, ["init", str(ws_path)])
    assert result_init.exit_code == 0

    # First create ok
    result_create1 = runner.invoke(
        main_app, ["create", "agent", "dup", "--workspace", str(ws_path)]
    )
    assert result_create1.exit_code == 0, result_create1.output

    # Second create should fail
    result_create2 = runner.invoke(
        main_app, ["create", "agent", "dup", "--workspace", str(ws_path)]
    )
    assert result_create2.exit_code != 0
    assert "already exists" in result_create2.output


def test_cli_dev_check_fails_outside_workspace(tmp_path: Path) -> None:
    runner = CliRunner()
    # Run from a plain directory (no forge.toml, no agents)
    result = runner.invoke(main_app, ["dev", "--check"], env={"PWD": str(tmp_path)})
    assert result.exit_code != 0
    assert (
        "not a workspace" in result.output.lower() or "missing" in result.output.lower()
    )


def test_cli_dev_check_passes_in_workspace(tmp_path: Path) -> None:
    runner = CliRunner()
    ws_path = tmp_path / "ws"
    result_init = runner.invoke(main_app, ["init", str(ws_path)])
    assert result_init.exit_code == 0

    # Should succeed when checking in a valid workspace
    result = runner.invoke(main_app, ["dev", "--check", "--workspace", str(ws_path)])
    assert result.exit_code == 0, result.output
    assert (
        "dev mode ready" in result.output.lower()
        or "validated" in result.output.lower()
    )


def test_cli_dev_run_for_logs_events(tmp_path: Path, monkeypatch) -> None:
    runner = CliRunner()
    ws_path = tmp_path / "ws"

    # init workspace and a starter agent
    result_init = runner.invoke(main_app, ["init", str(ws_path)])
    assert result_init.exit_code == 0
    (ws_path / "agents" / "demo").mkdir(parents=True)
    demo_py = ws_path / "agents" / "demo" / "agent.py"
    demo_py.write_text("print('hi')\n", encoding="utf-8")

    # Run dev for a short time and touch a file to trigger logs
    result = runner.invoke(
        main_app,
        ["dev", "--workspace", str(ws_path), "--run-for", "0.5"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    # Output should mention watching
    assert "watching" in result.output.lower()


def test_cli_dev_hot_reload_stub_on_agent_change(tmp_path: Path) -> None:
    runner = CliRunner()
    ws_path = tmp_path / "ws"

    # init workspace and demo agent
    result_init = runner.invoke(main_app, ["init", str(ws_path)])
    assert result_init.exit_code == 0
    demo_dir = ws_path / "agents" / "demo"
    demo_dir.mkdir(parents=True)
    demo_py = demo_dir / "agent.py"
    demo_py.write_text("print('hi')\n", encoding="utf-8")

    # Run dev for a short time and explicitly touch the agent file via --test-touch to trigger reload
    result = runner.invoke(
        main_app,
        [
            "dev",
            "--workspace",
            str(ws_path),
            "--run-for",
            "0.5",
            "--test-touch",
            str(demo_py),
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    assert "loaded agent: demo" in result.output.lower()
    assert "reloaded agent: demo" in result.output.lower()


def test_cli_dev_registers_agents(tmp_path: Path) -> None:
    runner = CliRunner()
    ws_path = tmp_path / "ws"

    # init workspace and demo agent
    result_init = runner.invoke(main_app, ["init", str(ws_path)])
    assert result_init.exit_code == 0
    demo_dir = ws_path / "agents" / "demo"
    demo_dir.mkdir(parents=True)
    (demo_dir / "agent.py").write_text(
        (
            """
from l6e_forge.types.core import AgentContext, AgentResponse, Message

class Agent:
    name = "demo"
    async def handle_message(self, message: Message, context: AgentContext) -> AgentResponse:
        return AgentResponse(content="ok", agent_id=self.name, response_time=0.0)
"""
        ).strip(),
        encoding="utf-8",
    )

    # Run dev briefly
    result = runner.invoke(
        main_app,
        ["dev", "--workspace", str(ws_path), "--run-for", "0.5"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    out = result.output.lower()
    assert "loaded agent: demo" in out or "watching" in out
    assert "registered agent: demo" in out


def test_cli_chat_message_roundtrip(tmp_path: Path) -> None:
    runner = CliRunner()
    ws_path = tmp_path / "ws"

    # init and create a simple agent
    result_init = runner.invoke(main_app, ["init", str(ws_path)])
    assert result_init.exit_code == 0

    demo_dir = ws_path / "agents" / "demo"
    demo_dir.mkdir(parents=True)
    (demo_dir / "agent.py").write_text(
        (
            """
from l6e_forge.types.core import AgentContext, AgentResponse, Message

class Agent:
    name = "demo"
    description = "demo"
    version = "0.0.1"

    async def initialize(self, runtime):
        pass

    async def handle_message(self, message: Message, context: AgentContext) -> AgentResponse:
        return AgentResponse(content=f"Echo: {message.content}", agent_id=self.name, response_time=0.0)
"""
        ).strip(),
        encoding="utf-8",
    )

    result = runner.invoke(
        main_app,
        ["chat", "demo", "--workspace", str(ws_path), "--message", "hello"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    assert "Echo: hello" in result.output


def test_cli_chat_uses_agent_config_defaults(tmp_path: Path) -> None:
    # Prepare workspace and agent config pointing to a provider/model that will fail fast
    ws_path = tmp_path / "ws"
    ws_path.mkdir(parents=True)
    agents_dir = ws_path / "agents" / "demo"
    agents_dir.mkdir(parents=True)
    (agents_dir / "agent.py").write_text(
        (
            """
from l6e_forge.types.core import AgentContext, AgentResponse, Message

class Agent:
    name = "demo"
    async def handle_message(self, message: Message, context: AgentContext) -> AgentResponse:
        return AgentResponse(content="ok", agent_id=self.name, response_time=0.0)
"""
        ).strip(),
        encoding="utf-8",
    )
    (agents_dir / "config.toml").write_text(
        """
[agent]
provider = "lmstudio"
model = "dummy-model"
""".strip(),
        encoding="utf-8",
    )
    # Force an unreachable endpoint so the provider path fails deterministically
    (ws_path / "forge.toml").write_text(
        """
[models.endpoints]
lmstudio = "http://127.0.0.1:9"
""".strip(),
        encoding="utf-8",
    )

    # Without lmstudio server running, expect a helpful error (not a crash)
    from typer.testing import CliRunner
    from l6e_forge_cli.main import app as main_app

    runner = CliRunner()
    result = runner.invoke(
        main_app,
        ["chat", "demo", "--workspace", str(ws_path), "--message", "hi"],
        catch_exceptions=False,
    )
    # Exit code non-zero due to provider unreachable
    assert result.exit_code != 0
    out = result.output.lower()
    assert "lm studio" in out or "unreachable" in out or "failed" in out


def test_local_runtime_register_and_route(tmp_path: Path) -> None:
    # Create a minimal agent
    agent_dir = tmp_path / "demo"
    agent_dir.mkdir(parents=True)
    (agent_dir / "agent.py").write_text(
        (
            """
from l6e_forge.types.core import AgentContext, AgentResponse, Message

class Agent:
    name = "demo"
    description = "demo"
    version = "0.0.1"

    async def handle_message(self, message: Message, context: AgentContext) -> AgentResponse:
        return AgentResponse(content=message.content.upper(), agent_id=self.name, response_time=0.0)
"""
        ).strip(),
        encoding="utf-8",
    )

    rt = LocalRuntime()

    import asyncio

    async def _run():
        agent_id = await rt.register_agent(agent_dir)
        resp = await rt.route_message(
            Message(content="hi", role="user"), target=agent_id
        )
        return resp.content

    content = asyncio.run(_run())
    assert content == "HI"
