from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from l6e_forge_cli.main import app as main_app


def _write_min_agent(dir_path: Path, name: str = "demo") -> Path:
    agent_dir = dir_path / name
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "agent.py").write_text(
        (
            """
from l6e_forge.types.core import AgentContext, AgentResponse, Message

class Agent:
    name = "{name}"
    async def handle_message(self, message: Message, context: AgentContext) -> AgentResponse:
        return AgentResponse(content="ok", agent_id=self.name, response_time=0.0)
"""
        )
        .strip()
        .format(name=name),
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
    result_inspect = runner.invoke(
        main_app, ["pkg", "inspect", str(pkg_path)], catch_exceptions=False
    )
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
    import zipfile
    import io as _io
    import tomllib as _tomllib

    with zipfile.ZipFile(pkg_path2, "r") as zf:
        with zf.open("package.toml") as f:
            data = _tomllib.load(_io.BytesIO(f.read()))
    assert "agent_config" in data
    assert data["agent_config"]["agent"]["description"] == "Config Desc"
    assert data["agent_config"]["model"]["provider"] == "ollama"

    # Use CLI --show-config to display the embedded config
    result_show_cfg = runner.invoke(
        main_app,
        ["pkg", "inspect", str(pkg_path2), "--show-config"],
        catch_exceptions=False,
    )
    assert result_show_cfg.exit_code == 0, result_show_cfg.output
    out_cfg = result_show_cfg.output
    assert "[agent_config]" in out_cfg
    assert 'description = "Config Desc"' in out_cfg
    assert 'provider = "ollama"' in out_cfg


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
    result_init = runner.invoke(
        main_app, ["init", str(ws_path)], catch_exceptions=False
    )
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
    result = runner.invoke(
        main_app, ["pkg", "build", str(empty_dir)], catch_exceptions=False
    )
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
    assert (
        "not a workspace" in result_install.output.lower()
        or "missing" in result_install.output.lower()
    )


def test_pkg_checksums_present_and_inspect_counts(tmp_path: Path) -> None:
    runner = CliRunner()
    agent_dir = _write_min_agent(tmp_path / "src", name="csdemo")
    dist_dir = tmp_path / "dist"

    # Build without extra files -> expect 2 checksum entries (package.toml + agent/agent.py)
    result_build = runner.invoke(
        main_app,
        ["pkg", "build", str(agent_dir), "--out", str(dist_dir), "--version", "0.0.1"],
        catch_exceptions=False,
    )
    assert result_build.exit_code == 0, result_build.output
    pkg_path = dist_dir / "csdemo-0.0.1.l6e"
    assert pkg_path.exists()

    # Open and check checksums.txt exists and has 2 lines
    import zipfile

    with zipfile.ZipFile(pkg_path, "r") as zf:
        with zf.open("checksums.txt") as f:
            lines = f.read().decode("utf-8").strip().splitlines()
    assert len(lines) == 2
    assert any("package.toml" in ln for ln in lines)
    assert any("agent/agent.py" in ln for ln in lines)

    # Inspect summary shows count
    result_inspect = runner.invoke(
        main_app, ["pkg", "inspect", str(pkg_path)], catch_exceptions=False
    )
    assert result_inspect.exit_code == 0
    assert "Checksums" in result_inspect.output
    assert "(2 entries)" in result_inspect.output


def test_pkg_profiles_with_compose_and_requirements(tmp_path: Path) -> None:
    runner = CliRunner()
    agent_dir = _write_min_agent(tmp_path / "src", name="layered")
    dist_dir = tmp_path / "dist"
    req = tmp_path / "req.txt"
    req.write_text("requests==2.32.3\n", encoding="utf-8")

    # Build medium with compose overlay
    result_build_medium = runner.invoke(
        main_app,
        [
            "pkg",
            "build",
            str(agent_dir),
            "--out",
            str(dist_dir),
            "--version",
            "0.0.2",
            "--profile",
            "medium",
            "--include-compose",
            "--compose-services",
            "monitor,redis",
        ],
        catch_exceptions=False,
    )
    assert result_build_medium.exit_code == 0, result_build_medium.output
    pkg_medium = dist_dir / "layered-0.0.2.l6e"
    assert pkg_medium.exists()
    # Verify compose exists
    import zipfile

    with zipfile.ZipFile(pkg_medium, "r") as zf:
        assert "compose/stack.yaml" in zf.namelist()
        with zf.open("package.toml") as f:
            import tomllib as _toml

            data = _toml.load(f)
            assert data.get("artifacts", {}).get("profile") == "medium"
            assert data.get("compose", {}).get("file") == "compose/stack.yaml"

    # Build fat with requirements
    result_build_fat = runner.invoke(
        main_app,
        [
            "pkg",
            "build",
            str(agent_dir),
            "--out",
            str(dist_dir),
            "--version",
            "0.0.3",
            "--profile",
            "fat",
            "--requirements",
            str(req),
        ],
        catch_exceptions=False,
    )
    assert result_build_fat.exit_code == 0, result_build_fat.output
    pkg_fat = dist_dir / "layered-0.0.3.l6e"
    assert pkg_fat.exists()
    with zipfile.ZipFile(pkg_fat, "r") as zf:
        assert "artifacts/requirements.txt" in zf.namelist()
        with zf.open("package.toml") as f:
            import tomllib as _toml

            data = _toml.load(f)
            assert data.get("artifacts", {}).get("profile") == "fat"
            assert (
                data.get("artifacts", {}).get("requirements")
                == "artifacts/requirements.txt"
            )


def test_pkg_compose_auto_infers_qdrant_and_ollama(tmp_path: Path) -> None:
    runner = CliRunner()
    agent_dir = _write_min_agent(tmp_path / "src", name="auto1")
    # config: qdrant + ollama
    (agent_dir / "config.toml").write_text(
        (
            """
[agent]
name = "auto1"

[memory]
provider = "qdrant"

[model]
provider = "ollama"
model = "llama3.2:3b"
"""
        ).strip(),
        encoding="utf-8",
    )
    dist_dir = tmp_path / "dist"
    result_build = runner.invoke(
        main_app,
        [
            "pkg",
            "build",
            str(agent_dir),
            "--out",
            str(dist_dir),
            "--version",
            "0.0.4",
            "--include-compose",
            "--compose-services",
            "auto",
        ],
        catch_exceptions=False,
    )
    assert result_build.exit_code == 0, result_build.output
    pkg_path = dist_dir / "auto1-0.0.4.l6e"
    import zipfile

    with zipfile.ZipFile(pkg_path, "r") as zf:
        with zf.open("package.toml") as f:
            import tomllib as _toml

            data = _toml.load(f)
            svcs = data.get("compose", {}).get("services", [])
            assert "monitor" in svcs
            assert "qdrant" in svcs
            assert "ollama" in svcs
            assert "redis" not in svcs
        text = zf.read("compose/stack.yaml").decode("utf-8")
        assert "qdrant:" in text
        assert "ollama:" in text
        assert "redis:" not in text


def test_pkg_compose_auto_infers_redis_only(tmp_path: Path) -> None:
    runner = CliRunner()
    agent_dir = _write_min_agent(tmp_path / "src", name="auto2")
    # config: redis memory only
    (agent_dir / "config.toml").write_text(
        (
            """
[agent]
name = "auto2"

[memory]
provider = "redis"
"""
        ).strip(),
        encoding="utf-8",
    )
    dist_dir = tmp_path / "dist"
    result_build = runner.invoke(
        main_app,
        [
            "pkg",
            "build",
            str(agent_dir),
            "--out",
            str(dist_dir),
            "--version",
            "0.0.5",
            "--include-compose",
            "--compose-services",
            "auto",
        ],
        catch_exceptions=False,
    )
    assert result_build.exit_code == 0, result_build.output
    pkg_path = dist_dir / "auto2-0.0.5.l6e"
    import zipfile

    with zipfile.ZipFile(pkg_path, "r") as zf:
        with zf.open("package.toml") as f:
            import tomllib as _toml

            data = _toml.load(f)
            svcs = data.get("compose", {}).get("services", [])
            assert "monitor" in svcs
            assert "redis" in svcs
            assert "qdrant" not in svcs
            assert "ollama" not in svcs
        text = zf.read("compose/stack.yaml").decode("utf-8")
        assert "redis:" in text
        assert "qdrant:" not in text
        assert "ollama:" not in text


def test_pkg_install_verifies_checksums_and_detects_mismatch(tmp_path: Path) -> None:
    runner = CliRunner()
    agent_dir = _write_min_agent(tmp_path / "src", name="tamper")
    dist_dir = tmp_path / "dist"

    # Build
    result_build = runner.invoke(
        main_app,
        ["pkg", "build", str(agent_dir), "--out", str(dist_dir), "--version", "0.0.1"],
        catch_exceptions=False,
    )
    assert result_build.exit_code == 0, result_build.output
    pkg_path = dist_dir / "tamper-0.0.1.l6e"
    assert pkg_path.exists()

    # Prepare workspace
    ws_path = tmp_path / "ws"
    result_init = runner.invoke(
        main_app, ["init", str(ws_path)], catch_exceptions=False
    )
    assert result_init.exit_code == 0

    # First install should pass verification
    result_install_ok = runner.invoke(
        main_app,
        ["pkg", "install", str(pkg_path), "--workspace", str(ws_path)],
        catch_exceptions=False,
    )
    assert result_install_ok.exit_code == 0, result_install_ok.output
    assert "Checksum verification passed" in result_install_ok.output

    # Create a tampered package: replace agent/agent.py content but keep checksums.txt
    import zipfile

    tampered = dist_dir / "tamper-0.0.1-tampered.l6e"
    with (
        zipfile.ZipFile(pkg_path, "r") as zf_in,
        zipfile.ZipFile(tampered, "w") as zf_out,
    ):
        for info in zf_in.infolist():
            with zf_in.open(info.filename) as src:
                data = src.read()
            if info.filename == "agent/agent.py":
                data = b"print('tampered')\n"
            zf_out.writestr(info.filename, data)

    # Install tampered should fail checksum verification
    result_install_bad = runner.invoke(
        main_app,
        ["pkg", "install", str(tampered), "--workspace", str(ws_path)],
        catch_exceptions=False,
    )
    assert result_install_bad.exit_code != 0
    assert "checksum mismatch" in result_install_bad.output.lower()


def test_pkg_sign_and_verify_signature(tmp_path: Path, monkeypatch) -> None:
    runner = CliRunner()
    agent_dir = _write_min_agent(tmp_path / "src", name="signed")
    dist_dir = tmp_path / "dist"

    # Generate a signing key using PyNaCl
    try:
        from nacl.signing import SigningKey  # type: ignore
    except Exception:
        # If PyNaCl isn't available in the test env, skip gracefully
        import pytest  # type: ignore

        pytest.skip("PyNaCl not available")
        return

    sk = SigningKey.generate()
    # Write private as 32-byte seed (required by SigningKey()) and public as hex
    seed = sk._seed  # type: ignore[attr-defined]
    pk_bytes = sk.verify_key.encode()
    key_path = tmp_path / "sk.key"
    pub_path = tmp_path / "pk.key"
    key_path.write_text(seed.hex(), encoding="utf-8")
    pub_path.write_text(pk_bytes.hex(), encoding="utf-8")

    # Build signed package
    result_build = runner.invoke(
        main_app,
        [
            "pkg",
            "build",
            str(agent_dir),
            "--out",
            str(dist_dir),
            "--version",
            "0.0.1",
            "--sign-key",
            str(key_path),
        ],
        catch_exceptions=False,
    )
    assert result_build.exit_code == 0, result_build.output
    pkg_path = dist_dir / "signed-0.0.1.l6e"
    assert pkg_path.exists()

    # Prepare workspace
    ws_path = tmp_path / "ws"
    result_init = runner.invoke(
        main_app, ["init", str(ws_path)], catch_exceptions=False
    )
    assert result_init.exit_code == 0

    # Verify signature using embedded pub key
    result_install_sig = runner.invoke(
        main_app,
        [
            "pkg",
            "install",
            str(pkg_path),
            "--workspace",
            str(ws_path),
            "--verify-sig",
        ],
        catch_exceptions=False,
    )
    assert result_install_sig.exit_code == 0, result_install_sig.output
    assert "Signature verification passed" in result_install_sig.output

    # Verify signature using provided key path (ignoring embedded)
    result_install_sig2 = runner.invoke(
        main_app,
        [
            "pkg",
            "install",
            str(pkg_path),
            "--workspace",
            str(ws_path),
            "--verify-sig",
            "--overwrite",
            "--public-key",
            str(pub_path),
        ],
        catch_exceptions=False,
    )
    assert result_install_sig2.exit_code == 0, result_install_sig2.output
    assert "Signature verification passed" in result_install_sig2.output
