from __future__ import annotations

from typing import Protocol


class IProviderTemplate(Protocol):
    """Provider template plugin interface.

    Produces Jinja variables used by provider-flexible agent templates.
    """

    name: str

    def get_template_vars(self, model: str, endpoint: str | None) -> dict[str, str]:
        """Return variables like 'model_imports' and 'model_usage'."""
        ...
