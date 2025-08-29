from typing import Any, Protocol


class ILogManager(Protocol):
    """Log manager interface"""

    def log(
        self, level: str, message: str, context: dict[str, Any] | None = None
    ) -> None:
        """Log a message"""
        ...

    def get_logs(
        self, level: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Get log entries"""
        ...

    async def configure_logging(self, config: dict[str, Any]) -> None:
        """Configure logging settings"""
        ...
