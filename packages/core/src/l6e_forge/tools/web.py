from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import asyncio

import urllib.request
import urllib.error

from l6e_forge.tools.base import ITool
from l6e_forge.types.tool import ToolContext, ToolResult


@dataclass
class WebFetchTool(ITool):
    name: str = "web.fetch"
    description: str = "Fetch a webpage over HTTP(S) and return text content"
    category: str = "web"
    version: str = "0.1.0"

    def get_parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "timeout": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 60,
                    "default": 20,
                },
                "headers": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                },
            },
            "required": ["url"],
            "additionalProperties": False,
        }

    def get_return_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "status": {"type": "integer"},
                "content_type": {"type": "string"},
                "text": {"type": "string"},
            },
            "required": ["url", "status"],
        }

    async def validate_parameters(self, parameters: dict[str, Any]) -> bool:
        url = parameters.get("url")
        return isinstance(url, str) and (
            url.startswith("http://") or url.startswith("https://")
        )

    async def initialize(self) -> None:  # pragma: no cover
        return None

    async def cleanup(self) -> None:  # pragma: no cover
        return None

    async def execute(
        self, parameters: dict[str, Any], context: ToolContext
    ) -> ToolResult:
        if not context.allow_network:
            return ToolResult(
                success=False, error_message="Network access disabled in context"
            )
        if not await self.validate_parameters(parameters):
            return ToolResult(success=False, error_message="Invalid parameters")

        url: str = parameters["url"]
        timeout: int = int(parameters.get("timeout", 20))
        headers: dict[str, str] = {
            str(k): str(v) for k, v in (parameters.get("headers") or {}).items()
        }

        # Domain allow-list enforcement if present
        if context.allowed_domains:
            from urllib.parse import urlparse

            hostname = urlparse(url).hostname or ""
            allowed = any(
                hostname == d.replace("*.", "") or hostname.endswith(d.replace("*", ""))
                for d in context.allowed_domains
            )
            if not allowed:
                return ToolResult(
                    success=False, error_message="Domain not allowed by policy"
                )

        def _fetch() -> tuple[int, str, str]:
            req = urllib.request.Request(
                url, headers=headers or {"User-Agent": "l6e-forge/0.1"}
            )
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    status = resp.getcode() or 0
                    ctype = resp.headers.get("Content-Type", "")
                    body_bytes = resp.read()
                    # Attempt to decode as text
                    text = body_bytes.decode("utf-8", errors="replace")
                    return status, ctype, text
            except urllib.error.HTTPError as he:  # pragma: no cover - passthrough
                return he.code, str(he.headers or ""), str(he)
            except Exception as exc:  # pragma: no cover - safety
                return 0, "", f"ERROR: {exc}"

        status, content_type, text = await asyncio.to_thread(_fetch)
        if status == 0:
            return ToolResult(success=False, error_message=text)
        text_out = text[: context.max_output_size]
        return ToolResult(
            success=True,
            data={
                "url": url,
                "status": status,
                "content_type": content_type,
                "text": text_out,
            },
        )
