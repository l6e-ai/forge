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


class LMStudioModelManager(IModelManager):
    """Minimal LM Studio model manager using OpenAI-compatible API.

    Defaults to http://localhost:1234/v1 as commonly used by LM Studio.
    """

    def __init__(self, endpoint: str = "http://localhost:1234/v1") -> None:
        self.endpoint = endpoint.rstrip("/")
        self._models: dict[str, _LoadedModel] = {}

    async def load_model(self, model_spec: ModelSpec) -> uuid.UUID:
        model_id = uuid.uuid4()
        self._models[str(model_id)] = _LoadedModel(
            model_name=model_spec.model_name, spec=model_spec
        )
        return model_id

    async def unload_model(self, model_id: uuid.UUID) -> None:  # noqa: ARG002
        self._models.pop(str(model_id), None)

    async def reload_model(self, model_id: uuid.UUID) -> None:  # noqa: ARG002
        return None

    async def complete(self, model_id: uuid.UUID, prompt: str, **kwargs) -> Any:  # noqa: D401, ANN401
        raise NotImplementedError

    async def chat(
        self, model_id: uuid.UUID, messages: list[Message], **kwargs
    ) -> ChatResponse:
        loaded = self._models.get(str(model_id))
        if not loaded:
            raise RuntimeError("Model not loaded")

        url = f"{self.endpoint}/chat/completions"
        payload = {
            "model": loaded.model_name,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
        }
        payload.update({k: v for k, v in kwargs.items() if v is not None})

        timeout = kwargs.pop("timeout", 120.0)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
        except httpx.ConnectError as exc:  # noqa: PERF203
            raise RuntimeError(
                f"LM Studio server not reachable at {self.endpoint}. Start it and enable the OpenAI-compatible API."
            ) from exc
        except httpx.ReadTimeout as exc:
            raise RuntimeError(f"LM Studio request timed out after {timeout}s") from exc
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"LM Studio error: HTTP {exc.response.status_code} - {exc.response.text}"
            ) from exc

        data = resp.json()
        # Expected schema: choices[0].message.content
        choice = (data.get("choices") or [{}])[0]
        msg = choice.get("message") or {}
        content = msg.get("content", "")
        role = msg.get("role", "assistant")
        reply = Message(content=content, role=role)

        return ChatResponse(
            message=reply,
            model_id=str(model_id),
            request_id=data.get("id", str(uuid.uuid4())),
            tokens_generated=0,
            generation_time=0.0,
            tokens_per_second=0.0,
            finish_reason=choice.get("finish_reason", "completed"),
            prompt_tokens=0,
            context_used=len(messages),
            context_truncated=False,
        )

    async def stream_complete(self, model_id: uuid.UUID, prompt: str, **kwargs):  # noqa: D401, ANN201
        raise NotImplementedError

    def list_available_models(self) -> list[ModelSpec]:
        # OpenAI-compatible: GET /models
        try:
            resp = httpx.get(f"{self.endpoint}/models", timeout=5.0)
            resp.raise_for_status()
            data = resp.json()
            items = data.get("data", [])
        except Exception:
            return []

        specs: list[ModelSpec] = []
        for item in items:
            name = item.get("id") or item.get("name") or "unknown"
            specs.append(
                ModelSpec(
                    model_id=name,
                    provider="lmstudio",
                    model_name=name,
                    memory_requirement_gb=0.0,
                    provider_metadata=item,
                )
            )
        return specs

    def get_model_info(self, model_id: uuid.UUID) -> ModelInstance:
        loaded = self._models.get(str(model_id))
        if not loaded:
            raise RuntimeError("Model not loaded")
        from datetime import datetime

        return ModelInstance(
            model_id=str(model_id),
            spec=loaded.spec,
            status="ready",
            loaded_at=datetime.now(),
            last_used=datetime.now(),
        )

    async def get_model_health(self, model_id: uuid.UUID) -> HealthStatus:  # noqa: ARG002
        try:
            resp = httpx.get(f"{self.endpoint}/models", timeout=2.0)
            resp.raise_for_status()
            return HealthStatus(healthy=True, status="healthy")
        except Exception:
            return HealthStatus(
                healthy=False, status="unhealthy", errors=["LM Studio API unreachable"]
            )  # type: ignore[arg-type]

    def get_memory_usage(self) -> dict[uuid.UUID, int]:
        return {}

    async def optimize_memory(self) -> None:
        return None
