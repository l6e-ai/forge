from typing import AsyncIterator, Protocol

from l6e_forge.types.core import ModelID, Message
from l6e_forge.types.model import (
    ChatResponse,
    CompletionResponse,
    ModelInstance,
    ModelSpec,
)
from l6e_forge.types.error import HealthStatus


class IModelManager(Protocol):
    """Model manager interface protocol"""

    # Model lifecycle
    async def load_model(self, model_spec: ModelSpec) -> ModelID:
        """Load a model and return its ID"""
        ...

    async def unload_model(self, model_id: ModelID) -> None:
        """Unload a model from memory"""
        ...

    async def reload_model(self, model_id: ModelID) -> None:
        """Reload a model"""
        ...

    # Text generation
    async def complete(
        self, model_id: ModelID, prompt: str, **kwargs
    ) -> CompletionResponse:
        """Generate text completion"""
        ...

    async def chat(
        self, model_id: ModelID, messages: list[Message], **kwargs
    ) -> ChatResponse:
        """Generate chat response"""
        ...

    async def stream_complete(
        self, model_id: ModelID, prompt: str, **kwargs
    ) -> AsyncIterator[str]:
        """Stream text completion"""
        ...

    # Model information
    def list_available_models(self) -> list[ModelSpec]:
        """List all available models"""
        ...

    def get_model_info(self, model_id: ModelID) -> ModelInstance:
        """Get information about a loaded model"""
        ...

    async def get_model_health(self, model_id: ModelID) -> HealthStatus:
        """Check model health"""
        ...

    # Resource management
    def get_memory_usage(self) -> dict[ModelID, int]:
        """Get memory usage for each loaded model"""
        ...

    async def optimize_memory(self) -> None:
        """Optimize memory usage across models"""
        ...
