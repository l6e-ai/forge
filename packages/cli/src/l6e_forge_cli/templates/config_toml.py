from __future__ import annotations

CONFIG_TOML = """
[agent]
name = "{{ name }}"
version = "0.1.0"

[model]
provider = "{{ provider }}"
model = "{{ model }}"

[model.auto]
# Opt-in to automatic local model selection & bootstrap
enabled = true
providers = ["ollama"]
quality = "balanced"

[memory]
# Embedding model will be filled by bootstrapper if not set
embedding_model = ""
"""
