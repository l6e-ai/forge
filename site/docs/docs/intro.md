---
sidebar_position: 0
title: Introduction
description: Overview of L6E Forge and quick links to setup, CLI, packaging, and prompting.
---

## L6E Forge: Getting Started

Build, package, and run AI agents locally with Forge.

## Prerequisites

- Python 3.13 (Poetry recommended)
- Optional: Docker (API/monitor/UI stack)
- Optional: Ollama or LM Studio (local LLMs)

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
poetry run forge create agent my-ollama --provider=ollama --model llama3.2:3b
```

## Bootstrap Models (optional)

```bash
poetry run forge models bootstrap agents/my-ollama --provider-order ollama,lmstudio --interactive
```

## Run the Stack (optional)

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

See the full docs for CLI, packaging, installing, and prompt building.
