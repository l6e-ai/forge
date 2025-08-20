from __future__ import annotations

import asyncio

from agent_forge.infra.compose import ComposeTemplateService, ComposeServiceSpec


def test_compose_template_renders_selected_services() -> None:
    svc = ComposeTemplateService()

    async def _run():
        return await svc.generate([
            ComposeServiceSpec(name="monitor"),
            ComposeServiceSpec(name="redis"),
        ])

    text = asyncio.run(_run())
    assert "version: '3.8'" in text
    assert "services:" in text
    assert "monitor:" in text
    assert "redis:" in text
    assert "qdrant:" not in text


