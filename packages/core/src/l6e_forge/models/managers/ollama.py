from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

import httpx

from l6e_forge.types.core import Message
from l6e_forge.types.model import ChatResponse, ModelInstance, ModelSpec
from l6e_forge.types.error import HealthStatus
from l6e_forge.models.managers.base import IModelManager


@dataclass
class _LoadedModel:
    model_name: str
    spec: ModelSpec


class OllamaModelManager(IModelManager):
    """Minimal Ollama model manager for MVP.

    - Assumes Ollama server at http://localhost:11434 by default
    - Provides basic list, load, chat, and health checks
    - Gracefully explains when Ollama is not running
    """

    def __init__(self, endpoint: str = "http://localhost:11434") -> None:
        self.endpoint = endpoint.rstrip("/")
        self._models: dict[str, _LoadedModel] = {}  # model_id -> loaded model

    # Model lifecycle
    async def load_model(self, model_spec: ModelSpec) -> uuid.UUID:
        model_id = uuid.uuid4()
        self._models[str(model_id)] = _LoadedModel(
            model_name=model_spec.model_name, spec=model_spec
        )
        return model_id

    async def unload_model(self, model_id: uuid.UUID) -> None:  # noqa: ARG002
        # Ollama manages memory itself; skeleton just forgets the mapping
        self._models.pop(str(model_id), None)

    async def reload_model(self, model_id: uuid.UUID) -> None:  # noqa: ARG002
        # No-op for now
        return None

    # Text generation
    async def complete(self, model_id: uuid.UUID, prompt: str, **kwargs) -> Any:  # noqa: D401, ANN401
        raise NotImplementedError

    async def chat(
        self, model_id: uuid.UUID, messages: list[Message], **kwargs
    ) -> ChatResponse:
        loaded = self._models.get(str(model_id))
        if not loaded:
            raise RuntimeError("Model not loaded")
        payload = {
            "model": loaded.model_name,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
        }
        # Allow overrides like temperature
        payload.update({k: v for k, v in kwargs.items() if v is not None})

        url = f"{self.endpoint}/api/chat"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
        except httpx.ConnectError as exc:  # noqa: PERF203
            raise RuntimeError(
                f"Ollama is not running at {self.endpoint}. Install from https://ollama.com and run 'ollama serve'."
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Ollama error: HTTP {exc.response.status_code} - {exc.response.text}"
            ) from exc

        data = resp.json()
        # Expected schema: { 'message': {'role': 'assistant', 'content': '...'}, 'total_duration': ns, ... }
        content = data.get("message", {}).get("content", "")
        role = data.get("message", {}).get("role", "assistant")
        reply = Message(content=content, role=role)
        # Time fields from ollama are in nanoseconds; convert roughly to seconds
        total_duration_ns = data.get("total_duration", 0) or 0
        generation_time = float(total_duration_ns) / 1e9
        return ChatResponse(
            message=reply,
            model_id=str(model_id),
            request_id=data.get("id", str(uuid.uuid4())),
            tokens_generated=data.get("eval_count", 0) or 0,
            generation_time=generation_time,
            tokens_per_second=(data.get("eval_count", 0) or 0) / generation_time
            if generation_time > 0
            else 0.0,
            finish_reason="completed",
            prompt_tokens=data.get("prompt_eval_count", 0) or 0,
            context_used=len(messages),
            context_truncated=False,
        )

    async def stream_complete(self, model_id: uuid.UUID, prompt: str, **kwargs):  # noqa: D401, ANN201
        raise NotImplementedError

    # Model information
    def list_available_models(self) -> list[ModelSpec]:
        url = f"{self.endpoint}/api/tags"
        try:
            resp = httpx.get(url, timeout=5.0)
            resp.raise_for_status()
            tags = resp.json().get("models", [])
        except Exception:
            # If unavailable, return an empty list instead of failing
            return []

        specs: list[ModelSpec] = []
        for item in tags:
            name = item.get("name") or item.get("model") or "unknown"
            size = item.get("size", None)
            specs.append(
                ModelSpec(
                    model_id=name,
                    provider="ollama",
                    model_name=name,
                    memory_requirement_gb=0.0,
                    size_bytes=size,
                    description=item.get("details", {}).get("family", ""),
                    provider_metadata=item,
                )
            )
        return specs

    def get_model_info(self, model_id: uuid.UUID) -> ModelInstance:
        loaded = self._models.get(str(model_id))
        if not loaded:
            raise RuntimeError("Model not loaded")
        # Skeleton info
        from datetime import datetime

        return ModelInstance(
            model_id=str(model_id),
            spec=loaded.spec,
            status="ready",
            loaded_at=datetime.now(),
            last_used=datetime.now(),
        )

    async def get_model_health(self, model_id: uuid.UUID) -> HealthStatus:  # noqa: ARG002
        # Check server availability only
        try:
            resp = httpx.get(f"{self.endpoint}/api/version", timeout=2.0)
            resp.raise_for_status()
            return HealthStatus(healthy=True, status="healthy")
        except Exception:
            return HealthStatus(
                healthy=False, status="unhealthy", errors=["Ollama unreachable"]
            )  # type: ignore[arg-type]

    # Resource management
    def get_memory_usage(self) -> dict[uuid.UUID, int]:  # noqa: D401
        return {}

    async def optimize_memory(self) -> None:  # noqa: D401
        return None
