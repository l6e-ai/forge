### Proposal: seamless “auto-model” bootstrapping

- Core idea
  - Detect system capabilities, read agent hints, pick best local OSS models, auto-install and wire them. Devs can opt-in once and stop thinking about models.

### UX
- forge models doctor → prints CPU/GPU/VRAM/RAM/disk and local runtimes (ollama/lmstudio present? versions).
- forge models bootstrap --agent agents/demo
  - If model unset, chooses chat + embedding models, pulls them (ollama by default), verifies, and updates `agents/demo/config.toml`.
- forge up --agents demo
  - If missing models, runs bootstrap automatically (non-interactive), shows pull progress, then starts.

### Agent hints (manifest/config)
- In `agents/<name>/config.toml` or `package.toml`:
```toml
[model.auto]
enabled = true
providers = ["ollama"]  # fallback order; can include "lmstudio", "openai"
task = "assistant"      # assistant, coder, rlhf, tool-use (affects choice)
quality = "balanced"    # speed, balanced, quality
context = 8192

# Optional explicit choices with constraints
[[model.choices]]
name = "llama3.2:3b"
min_ram_gb = 8
max_vram_gb = 0
preferred = true

[[model.choices]]
name = "llama3.1:8b-instruct"
min_vram_gb = 6
```

### Selection algorithm (summary)
- Detect:
  - CPU cores, RAM, free disk; GPU vendor (CUDA/ROCm/Metal) + VRAM; OS; internet.
  - Local runtimes: ollama daemon reachable? lmstudio? versions.
- Candidate matrix (curated defaults; kept in repo as data):
  - Chat:
    - CPU-only: llama3.2:3b (fast), qwen2.5:3b
    - Mid GPU (6–8 GB): llama3.1:8b-instruct, qwen2.5:7b-instruct
    - High GPU (>=16 GB): llama3.1:70b (optional), qwen2.5:32b (optional)
  - Embeddings: nomic-embed-text:latest (CPU ok), bge-m3 (optional)
- Filter by constraints + agent hints, pick best by heuristic: quality tier→context→speed score for hardware.

### Implementation plan (thin slice)
- New module `l6e_forge/models/auto.py`:
  - get_system_profile() → SystemProfile
  - recommend_models(profile, hints) → {chat, embedding}
  - bootstrap_models(provider, recommendations) for ollama:
    - Check daemon; if missing, prompt to install or print instructions (macOS: brew; Linux: docker compose service).
    - Pull tags via `ollama pull`; verify availability.
- CLI:
  - forge models doctor (uses get_system_profile)
  - forge models bootstrap --agent <dir> [--provider ollama] [--dry-run]
- Integrations:
  - forge up: auto-run bootstrap if `[model.auto.enabled]` and selected models not present.
  - Packaging: embed `[model.auto]` from config into `package.toml`. Our compose auto-infer already includes `ollama`; keep that when needed.

### Nice-to-have (later)
- LM Studio support: if LM Studio running, prefer using its models; otherwise fall back to Ollama.
- Remote fallback: if no local runtime viable, optionally switch to OpenAI/Anthropic with a helpful prompt.
- Cached downloads and progress UI in monitor.
- Per-agent wheelhouse + venv to ensure embeddings/tool deps work out of the box.

Want me to implement the thin slice (doctor + bootstrap + auto-run from forge up + default candidate matrix for Ollama) now?