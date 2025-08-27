---
sidebar_position: 1
title: Getting Started
---

<!-- Adapted from repo docs/getting-started.md -->

## Prerequisites

- Python 3.13 (Poetry recommended)
- Optional: Docker, Ollama or LM Studio

## Install

```bash
poetry install l6e-forge
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

## Run the Stack

```bash
poetry run forge up
```

API: http://localhost:8000 — Monitor: http://localhost:8321 — UI: http://localhost:8000/ui/

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


