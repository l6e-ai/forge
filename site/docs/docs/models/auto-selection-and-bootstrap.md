---
title: Auto model selection & bootstrapping
description: Use Forge to suggest, select, and configure local models automatically.
---

## Why auto-selection?

Local models vary in size, speed, and memory footprint. Forge can inspect your system, suggest options that fit, and update your agent's `config.toml` accordingly. It also helps ensure required Ollama models exist (pulling if needed).

## Quick start

Suggest models:

```bash
poetry run forge models suggest --quality balanced --top 5
```

Bootstrap an agent (configure `[model]` and embeddings in `config.toml`):

```bash
poetry run forge models bootstrap agents/my-ollama --provider-order ollama,lmstudio --interactive
```

- Use `--accept-best` for non-interactive selection.
- Use `--dry-run` to only print recommendations.

## What bootstrapping does

Under the hood, the CLI uses `l6e_forge.models.auto` to:

- Collect a `SystemProfile` (OS, cores, RAM, GPU/VRAM, installed providers)
- Build `AutoHints` from your flags (provider order, quality, quantization)
- Generate model suggestions with estimated memory and installed status
- If chosen model is Ollama and not present, try pulling alternates
- Update your agent's `config.toml` with:
  - `[model] provider` and `model` (chat)
  - `[memory] embedding_model`

After bootstrap, your agent code can request a model via the runtime model manager:

```python
manager = self.runtime.get_model_manager()
from l6e_forge.types.model import ModelSpec
spec = ModelSpec(
    model_id=self._model or "auto",
    provider=self._provider or "ollama",
    model_name=self._model or "llama3.2:3b",
    memory_requirement_gb=0.0,
)
model_id = await manager.load_model(spec)
```

## Flags and behaviors

- **`--provider-order`**: Preferred providers, e.g., `ollama,lmstudio`. Only available providers are considered.
- **`--quality`**: `speed | balanced | quality`. Influences simple ranking (smaller vs. larger parameter counts).
- **`--quant`**: `auto | q4 | q5 | q8 | mxfp4 | 8bit`. Guides memory estimates and tag choices.
- **`--interactive`**: Shows a list to pick from; uses TTY prompts when available.
- **`--accept-best`**: Non-interactive auto-accept top suggestion.
- **`--dry-run`**: Print table only; no config changes.

## How estimates are computed

`l6e_forge.models.auto` includes a small catalog with typical quantized artifact sizes (when known) and falls back to parameter-based estimates when not. For Ollama, installed model sizes are read from the local API when available for more accurate numbers.

The CLI displays:

- Estimated memory footprint and % of your available VRAM/RAM
- Whether the model likely fits locally
- Provider availability and whether the model is already installed

## Troubleshooting

- Ensure provider APIs are running (e.g., Ollama daemon, LM Studio server).
- If Ollama is selected but the exact tag is missing, Forge will try common alternates and pull them (`llama3.1:8b-instruct` → `llama3.1:8b`).
- If no suggestions are shown, verify network access and provider endpoints, then try `poetry run forge models doctor` to inspect your system profile.


