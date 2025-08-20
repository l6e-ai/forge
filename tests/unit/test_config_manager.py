from __future__ import annotations

from pathlib import Path
import textwrap
import pytest

from l6e_forge.config_managers.toml import TomlConfigManager


@pytest.mark.asyncio
async def test_load_and_get_values(tmp_path: Path) -> None:
    cfg = tmp_path / "forge.toml"
    cfg.write_text(
        textwrap.dedent(
            """
            [agent]
            name = "demo"
            model = "llama3.2:3b"
            
            [runtime]
            hot_reload = true
            """
        ).strip(),
        encoding="utf-8",
    )

    mgr = TomlConfigManager()
    data = await mgr.load_config(cfg)
    assert data["agent"]["name"] == "demo"
    assert mgr.get_config_value("agent.model") == "llama3.2:3b"
    assert mgr.get_config_value("runtime.hot_reload") is True
    assert mgr.get_config_value("not.there", default=123) == 123


