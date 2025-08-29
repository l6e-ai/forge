---
sidebar_position: 1
title: Getting Started
description: Create a workspace, scaffold an agent, bootstrap models, and run the stack.
---

<!-- Adapted from repo docs/getting-started.md -->

## Prerequisites

- Python 3.13 (Poetry recommended)
- Optional: Docker, Ollama or LM Studio

Set up a local LLM provider (recommended): [Local LLM providers](models/local-llm-providers)

## Install

```bash
# Add core library to your project
poetry add l6e-forge

# Add CLI as a dev dependency
poetry add --group dev l6e-forge-cli
```

Using uv:

```bash
uv add l6e-forge
uv add --dev l6e-forge-cli
```

Using pip:

```bash
pip install l6e-forge l6e-forge-cli
```

## Create a Workspace

```bash
poetry run forge init ./my-workspace
cd my-workspace
```

## Create an Agent

```bash
poetry run forge create agent my-assistant --template=assistant
poetry run forge create agent my-ollama --provider=ollama --model llama3.2:3b
```

## Bootstrap Models

```bash
poetry run forge models bootstrap agents/my-ollama --provider-order ollama,lmstudio --interactive
```

See more details on recommendations, flags, and how it updates your agent: [Auto model selection & bootstrapping](models/auto-selection-and-bootstrap)

## Run the Stack

```bash
poetry run forge up
```

API: http://localhost:8000 — Monitor: http://localhost:8321 — UI: http://localhost:8173

## Chat

```bash
poetry run forge chat my-ollama -w ./my-workspace
```

## Workspace Structure

```text
my-workspace/
├── forge.toml
├── agents/
│   └── my-ollama/
│       ├── agent.py
│       ├── config.toml
│       └── tools.py (optional)
└── .forge/
    ├── logs/
    └── data/
```


## Next steps

- Customize your agent and add few‑shot examples: [Customize your agent](agents/customize-agent)


