---
sidebar_position: 0
title: Introduction
description: Overview of L6E Forge and quick links to setup, CLI, packaging, and prompting.
slug: /
---

## L6E Forge at a Glance

⚒️ Build and run local‑first AI agents on your laptop.

🔌 Adapters‑first architecture: swap models, memory, and runtimes without rewrites.

📦 Ship portable `.l6e` bundles with optional UI and offline wheels.

🖥️ Optional local stack: API, monitor, and chat UI via Docker.

🧩 Bring your own providers: Ollama, LM Studio, Qdrant, Postgres, and more.

Forge is an open source toolkit for prototyping, packaging, and shipping AI agent MVPs. Start simple with a single process and scale components independently by switching adapters—no vendor lock‑in.

### Fast Track ⏱️
Understand Forge in 5 minutes by trying it locally.

#### Prerequisites
- Python 3.13 (Poetry recommended)
- Optional: Docker (for API/monitor/UI stack)
- Optional: Ollama or LM Studio (local LLMs)

#### Install a local LLM provider
We recommend Ollama for most users. See: [Local LLM providers](models/local-llm-providers)

#### Try it
```bash
# Add core library to your project
poetry add l6e-forge

# Add CLI as a dev dependency
poetry add --group dev l6e-forge-cli

# Create a new workspace
poetry run forge init ./my-workspace
cd my-workspace

# Create an agent (Ollama example)
poetry run forge create agent my-ollama --provider=ollama --model llama3.2:3b

# Chat locally (no Docker required)
poetry run forge chat my-ollama -w .
```

Alternative install methods:

Using uv:

```bash
uv add l6e-forge
uv add --dev l6e-forge-cli
```

Using pip:

```bash
pip install l6e-forge l6e-forge-cli
```

Optional: start the local stack with API, monitor, and UI.
```bash
poetry run forge up
# API: http://localhost:8000
# Monitor: http://localhost:8321
# UI: http://localhost:8173
```

:::tip
No GPU? Try smaller models (e.g., `llama3.2:1b`) or LM Studio quantized models.
:::

### What is Forge?
Forge is a batteries‑included set of tools to design agents, run them locally, and package them for distribution. It favors simple defaults and explicit adapters so you can tinker, replace, and scale parts of your system without rewriting agent logic.

### Key Features
- **Local‑first**: develop and run entirely on your machine.
- **Adapters‑first**: swap providers for models, memory, runners, and storage.
- **Optional full stack**: API, monitoring, and chat UI via Docker.
- **Packaging**: build portable `.l6e` bundles; optionally include a UI and Python wheels for offline installs.
- **Model helpers**: suggest and bootstrap Ollama/LM Studio models.
- **Memory API**: pluggable backends (e.g., in‑memory, Qdrant) with simple HTTP endpoints.

### Design Principles
- **Little to learn**: start with a single command; grow as needed.
- **Sensible defaults**: opinions that get you productive fast.
- **No lock‑in**: adapters let you switch components without rewrites.
- **Layered architecture**: clean separation of content, runtime, and storage.
- **Local‑first, scale‑out**: start on a laptop, scale components independently.

### When to use Forge
Use Forge if:
- ✅ You want a modern, local‑first agent toolkit
- ✅ You value portability and packaging (`.l6e` bundles)
- ✅ You want to tinker with and swap providers via adapters
- ✅ You are OK with the alpha API & SDK evolving - we will release a stable version soon, but right now we are iterating to make sure we get forge right.

### Learn More
- **Getting Started**: end‑to‑end walkthrough
- **CLI Reference**: commands for creating agents, packaging, and running the stack
- **Packaging Agents**: build and distribute `.l6e` bundles
- **Prompt Builder**: compose and load prompts

### Something missing?
Found an issue or have a suggestion? Please open a GitHub issue and help us improve the docs and the project.
