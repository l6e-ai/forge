---
title: Local LLM providers (Ollama & LM Studio)
description: Install and run Ollama or LM Studio for local models used by Forge.
---

## Overview

Forge works great with local providers. We recommend Ollama for most setups; LM Studio is also supported via its OpenAI-compatible server.

## Ollama (recommended)

1) Install Ollama:

```bash
# macOS
brew install ollama
ollama --version
```

2) Start the Ollama service (if not already running):

```bash
ollama serve
```

3) Pull a model:

```bash
ollama pull llama3.2:3b
```

4) Verify the API is reachable:

```bash
curl http://localhost:11434/api/tags | jq .
```

Tip: Set `OLLAMA_HOST` if your endpoint differs (default is `http://localhost:11434`).

## LM Studio

1) Install LM Studio from their website.

2) Open LM Studio and download a chat model (e.g., GPT‑OSS 20B or Llama variants).

3) Start the local server (OpenAI-compatible):

```text
Settings → Developer → Start Server
```

4) Note the server URL (default: `http://localhost:1234/v1`). You can set `LMSTUDIO_HOST` to override.

## Using with Forge

- When creating an agent, pick a provider and model:

```bash
poetry run forge create agent my-ollama --provider=ollama --model llama3.2:3b
```

- Or bootstrap recommendations for an existing agent:

```bash
poetry run forge models bootstrap agents/my-ollama --provider-order ollama,lmstudio --interactive
```

If using Docker for the full stack, ensure your provider is accessible from containers (e.g., host networking or proper `OLLAMA_HOST`/`LMSTUDIO_HOST`).


