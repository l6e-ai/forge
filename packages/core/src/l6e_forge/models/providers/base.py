from typing import Protocol

from l6e_forge.types.model import ModelInstance, ModelSpec


class IModelProvider(Protocol):
    """Model provider interface"""

    provider_name: str

    async def load_model(self, model_spec: ModelSpec) -> ModelInstance:
        """Load a model using this provider"""
        ...

    async def unload_model(self, model_instance: ModelInstance) -> None:
        """Unload a model"""
        ...

    def supports_model(self, model_spec: ModelSpec) -> bool:
        """Check if this provider supports the given model"""
        ...

    def get_available_models(self) -> list[ModelSpec]:
        """Get list of models available through this provider"""
        ...
