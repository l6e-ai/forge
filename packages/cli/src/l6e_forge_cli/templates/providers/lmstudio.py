from __future__ import annotations


class LMStudioProviderTemplate:
    name = "lmstudio"

    def get_template_vars(self, model: str, endpoint: str | None) -> dict[str, str]:
        imports = "from l6e_forge.models.managers.lmstudio import LMStudioModelManager"
        usage = """
        manager = self.runtime.get_model_manager() if hasattr(self, 'runtime') and self.runtime else LMStudioModelManager()
        from l6e_forge.types.model import ModelSpec
        spec = ModelSpec(model_id=\"{{ model }}\", provider=\"lmstudio\", model_name=\"{{ model }}\", memory_requirement_gb=0.0)
        model_id = await manager.load_model(spec)
        chat = await manager.chat(model_id, [message])
        return AgentResponse(content=chat.message.content, agent_id=self.name, response_time=0.0)
"""
        return {"model_imports": imports, "model_usage": usage}
