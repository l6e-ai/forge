---
sidebar_position: 1
---

# L6E Forge Quickstart

Kickstart building, packaging, and running AI agents locally.

## Prerequisites

- Python 3.13 with Poetry
- Optional: Docker (for running the full stack)
- Optional: Ollama or LM Studio (for local LLMs)

## Install CLI

```bash
poetry install l6e-forge
```

## Create a workspace

```bash
poetry run forge init ./my-workspace
cd my-workspace
```

## Create an agent

```bash
poetry run forge create agent my-ollama --provider=ollama --model llama3.2:3b
```

## Run the stack (optional)

```bash
poetry run forge up
```

- API: http://localhost:8000
- Monitor: http://localhost:8321
- UI: http://localhost:8000/ui/

## Chat with your agent

```bash
poetry run forge chat my-ollama -w ./my-workspace
```

For details, see the full Getting Started guide in the repository.
