from __future__ import annotations

from pathlib import Path
from typing import Any, Tuple
import os

from l6e_forge.models.managers.base import IModelManager


def load_endpoints_from_config(
    workspace_root: Path,
) -> Tuple[str | None, dict[str, str]]:
    """Return (default_provider, endpoints) from forge.toml if present."""
    default_provider: str | None = None
    endpoints: dict[str, str] = {}
    cfg_path = workspace_root / "forge.toml"
    if not cfg_path.exists():
        return default_provider, endpoints
    try:
        import tomllib

        with cfg_path.open("rb") as f:
            data = tomllib.load(f) or {}

        # Read simple keys synchronously to avoid un-awaited coroutine warnings in CLI
        def _get(d: dict, path: str):
            cur: Any = d
            for part in path.split("."):
                if not isinstance(cur, dict) or part not in cur:
                    return None
                cur = cur[part]
            return cur

        default_provider = _get(data, "models.default_provider")
        ollama_ep = _get(data, "models.endpoints.ollama")
        lmstudio_ep = _get(data, "models.endpoints.lmstudio")
        if isinstance(ollama_ep, str):
            endpoints["ollama"] = ollama_ep
        if isinstance(lmstudio_ep, str):
            endpoints["lmstudio"] = lmstudio_ep
    except Exception:
        pass
    return default_provider, endpoints


def get_manager(
    provider: str, endpoints: dict[str, str] | None = None
) -> IModelManager:
    """Construct a model manager for the given provider name using endpoints if provided."""
    p = provider.lower()
    eps = endpoints or {}
    if p == "ollama":
        from l6e_forge.models.managers.ollama import OllamaModelManager

        return OllamaModelManager(
            endpoint=eps.get(
                "ollama", os.environ.get("OLLAMA_HOST", "http://localhost:11434")
            )
        )
    if p == "lmstudio":
        from l6e_forge.models.managers.lmstudio import LMStudioModelManager

        return LMStudioModelManager(
            endpoint=eps.get(
                "lmstudio", os.environ.get("LMSTUDIO_HOST", "http://localhost:1234/v1")
            )
        )
    raise ValueError(f"Unsupported provider: {provider}")
