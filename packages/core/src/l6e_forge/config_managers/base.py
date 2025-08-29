from pathlib import Path
from typing import Any, Protocol


class IConfigManager(Protocol):
    """Configuration manager interface"""

    async def load_config(self, config_path: Path) -> dict[str, Any]:
        """Load configuration from file"""
        ...

    async def save_config(self, config: dict[str, Any], config_path: Path) -> None:
        """Save configuration to file"""
        ...

    async def validate_config(
        self, config: dict[str, Any], schema: dict[str, Any]
    ) -> bool:
        """Validate configuration against schema"""
        ...

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get a configuration value"""
        ...

    def set_config_value(self, key: str, value: Any) -> None:
        """Set a configuration value"""
        ...
