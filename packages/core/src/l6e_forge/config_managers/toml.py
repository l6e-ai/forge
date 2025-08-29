from __future__ import annotations

from pathlib import Path
from typing import Any

import tomllib

from l6e_forge.config_managers.base import IConfigManager


class TomlConfigManager(IConfigManager):
    def __init__(self) -> None:
        self._config: dict[str, Any] = {}

    async def load_config(self, config_path: Path) -> dict[str, Any]:
        path = Path(config_path).expanduser().resolve()
        if not path.exists():
            self._config = {}
            return self._config
        with path.open("rb") as f:
            data = tomllib.load(f)
        self._config = data or {}
        return self._config

    async def save_config(self, config: dict[str, Any], config_path: Path) -> None:  # noqa: D401
        # For MVP we won't write out config; CLI writes files directly
        self._config = config
        return None

    async def validate_config(
        self, config: dict[str, Any], schema: dict[str, Any]
    ) -> bool:  # noqa: D401
        # MVP: accept all configs
        return True

    def get_config_value(self, key: str, default: Any = None) -> Any:
        # Support dot-paths like "agent.model"
        parts = key.split(".")
        current: Any = self._config
        for p in parts:
            if not isinstance(current, dict) or p not in current:
                return default
            current = current[p]
        return current

    def set_config_value(self, key: str, value: Any) -> None:
        parts = key.split(".")
        current = self._config
        for p in parts[:-1]:
            current = current.setdefault(p, {})
        current[parts[-1]] = value
