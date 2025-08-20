import React from "react";
import Nav from "../../../components/Nav";
import Section from "../../../components/Section";
import Footer from "../../../components/Footer";
import CodeBlock from "../../../components/CodeBlock";

const adapterSkeletonPy = `# Python adapter: implement IModelManager to plug any SDK
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from l6e_forge.models.managers.base import IModelManager
from l6e_forge.types.model import ModelSpec, ModelInstance, ChatResponse
from l6e_forge.types.core import Message
from l6e_forge.types.error import HealthStatus


@dataclass
class _LoadedModel:
    model_name: str
    spec: ModelSpec


class MySDKModelManager(IModelManager):
    """Adapter that wraps your existing SDK/client into l6e-forge's interface.

    Required methods shown below; keep semantics consistent with your SDK.
    """

    def __init__(self, client: Any) -> None:
        self.client = client
        self._models: dict[str, _LoadedModel] = {}

    # --- Lifecycle ---
    async def load_model(self, model_spec: ModelSpec) -> uuid.UUID:
        model_id = uuid.uuid4()
        # Optionally ask your SDK to load/prepare here
        self._models[str(model_id)] = _LoadedModel(model_name=model_spec.model_name, spec=model_spec)
        return model_id

    async def unload_model(self, model_id: uuid.UUID) -> None:
        # Optionally instruct your SDK to release resources
        self._models.pop(str(model_id), None)

    async def reload_model(self, model_id: uuid.UUID) -> None:
        return None

    # --- Generation ---
    async def complete(self, model_id: uuid.UUID, prompt: str, **kwargs):
        raise NotImplementedError  # optional for MVP

    async def chat(self, model_id: uuid.UUID, messages: list[Message], **kwargs) -> ChatResponse:
        loaded = self._models.get(str(model_id))
        if not loaded:
            raise RuntimeError("Model not loaded")

        # Bridge your SDK call here; example assumes a chat(messages=[{"role":..., "content":...}]) API
        payload = {"model": loaded.model_name, "messages": [m.__dict__ for m in messages]}
        payload.update({k: v for k, v in kwargs.items() if v is not None})

        # result = await self.client.chat(**payload)
        # For illustration, construct a minimal response
        reply = Message(role="assistant", content="Hello from MySDK")
        return ChatResponse(
            message=reply,
            model_id=str(model_id),
            request_id=str(uuid.uuid4()),
            tokens_generated=0,
            generation_time=0.0,
            tokens_per_second=0.0,
            finish_reason="completed",
            prompt_tokens=0,
            context_used=len(messages),
            context_truncated=False,
        )

    async def stream_complete(self, model_id: uuid.UUID, prompt: str, **kwargs):
        raise NotImplementedError

    # --- Introspection ---
    def list_available_models(self) -> list[ModelSpec]:
        # Optionally list from your SDK; return [] if not supported
        return []

    def get_model_info(self, model_id: uuid.UUID) -> ModelInstance:
        from datetime import datetime
        loaded = self._models[str(model_id)]
        return ModelInstance(
            model_id=str(model_id),
            spec=loaded.spec,
            status="ready",
            loaded_at=datetime.now(),
            last_used=datetime.now(),
        )

    async def get_model_health(self, model_id: uuid.UUID) -> HealthStatus:
        return HealthStatus(healthy=True, status="healthy")

    # --- Resources ---
    def get_memory_usage(self) -> dict[uuid.UUID, int]:
        return {}

    async def optimize_memory(self) -> None:
        return None
`;

const usingBuiltinsPy = `# Using built-in providers (Ollama, LM Studio)
from pathlib import Path
from l6e_forge.models.providers.registry import get_manager, load_endpoints_from_config
from l6e_forge.types.model import ModelSpec
from l6e_forge.types.core import Message
import asyncio

workspace_root = Path.cwd()  # parent directory of your agents
default_provider, endpoints = load_endpoints_from_config(workspace_root)

# Pick a provider explicitly or use default_provider if present
manager = get_manager("ollama", endpoints)
model_id = asyncio.run(manager.load_model(ModelSpec(
    model_id="llama3", provider="ollama", model_name="llama3:8b", memory_requirement_gb=0.0
)))
resp = asyncio.run(manager.chat(model_id, [Message(role="user", content="Hello")]))
print(resp.message.content)
`;

export default function AdaptersDocPage() {
  return (
    <div className="min-h-screen font-sans bg-[#0a0a0a] text-white">
      <Nav />
      <main>
        <Section className="py-16">
          <h1 className="text-3xl font-bold mb-4">Adapters & Interfaces</h1>
          <p className="text-white/70 max-w-2xl mb-6">
            l6e focuses on interfaces over rewrites. To plug your own SDK or framework into l6e/forge, implement the Python <code className="font-mono">IModelManager</code> interface.
          </p>
          <h2 className="text-xl font-semibold mb-3">Adapter skeleton (Python)</h2>
          <CodeBlock code={adapterSkeletonPy} highlight language="python" themeName="dracula" />
          <h2 className="text-xl font-semibold mt-8 mb-3">Using built-in providers</h2>
          <p className="text-white/70 max-w-2xl mb-4">Ollama and LM Studio are available out-of-the-box via the provider registry and <code className="font-mono">forge.toml</code> endpoints.</p>
          <CodeBlock code={usingBuiltinsPy} highlight language="python" themeName="dracula" />
          <div className="mt-8 text-white/70">
            Learn more in our GitHub repository and examples. Contributions welcome!
          </div>
        </Section>
      </main>
      <Footer />
    </div>
  );
}


