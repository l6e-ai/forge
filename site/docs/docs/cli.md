---
sidebar_position: 2
title: CLI Reference
description: Commands for initializing workspaces, running dev stack, chatting, models, and packaging.
---

<!-- Sourced from repo docs/cli.md; trimmed for site formatting -->

> Note: The CLI is in alpha. Commands and flags may change.

## Installation

```bash
# Install core library (required by your project)
poetry add l6e-forge

# Install CLI as a dev dependency
poetry add --group dev l6e-forge-cli

poetry run forge --help
```

Using uv:

```bash
# Install core library
uv add l6e-forge

# Install CLI as a dev dependency
uv add --dev l6e-forge-cli

uv run forge --help
```

Using pip:

```bash
# Install into your (virtual) environment
pip install l6e-forge l6e-forge-cli

forge --help
```

## Workspace Structure

A workspace contains `forge.toml` and an `agents/` directory.

## Environment Variables

- `AF_COMPOSE_FILE` — compose path for `forge up/down`
- `AF_MONITOR_URL` — monitor base URL (default `http://localhost:8321`)
- `AF_API_URL` — API base URL (default `http://localhost:8000/api`)
- `OLLAMA_HOST` — Ollama endpoint (default `http://localhost:11434`)
- `LMSTUDIO_HOST` — LM Studio endpoint (default `http://localhost:1234/v1`)

## Commands

### forge init

```bash
forge init <workspace> [--with-example] [--with-compose/--no-with-compose]
```

### forge list

```bash
forge list
```

### forge up

```bash
forge up [--workspace|-w <workspace>] [--compose-file|-f <path>] \
  [--monitor-url <url>] [--no-dev] [--dev-only] [--build] [--open-ui]
```

### forge down

```bash
forge down [--compose-file|-f <path>] [--volumes|-v]
```

### forge create agent

```bash
forge create agent <agent> [--workspace <workspace>] [--provider ollama] \
  [--model llama3.2:3b] [--provider-endpoint <url>] [--template assistant] \
  [--include-compose/--no-include-compose] [--memory-provider qdrant|memory]
```

### forge template list

```bash
forge template list
```

### forge dev

```bash
forge dev [--workspace|-w <workspace>] [--check]
```

### forge chat

```bash
forge chat <agent> [--message|-m "hello"] [--workspace|-w <workspace>] \
  [--stream/--no-stream] [--monitor-url <url>] [--markdown/--no-markdown] \
  [--timeout <s>] [--debug]
```

## Models

### forge models list

```bash
forge models list [--provider ollama|lmstudio|all] [--endpoint <url>]
```

### forge models doctor

```bash
forge models doctor
```

### forge models suggest

```bash
forge models suggest [--provider "ollama,lmstudio"] \
  [--quality speed|balanced|quality] [--top <n>] \
  [--quant auto|q4|q5|q8|mxfp4|8bit]
```

### forge models bootstrap

```bash
forge models bootstrap <agent_dir> [--provider-order "ollama,lmstudio"] \
  [--quality speed|balanced|quality] [--quant auto|q4|q5|q8|mxfp4|8bit] \
  [--top <n>] [--interactive/--no-interactive] [--accept-best] [--dry-run]
```

## Packaging

### forge pkg build

```bash
forge pkg build <agent_dir> [--out|-o dist] [--name <name>] [--version|-v 0.1.0] \
  [--description <text>] [--sign-key <path>] [--profile thin|medium|fat] \
  [--include-compose] [--compose-services auto|<svc1,svc2>] \
  [--requirements <req.txt>] [--bundle-wheels/--no-bundle-wheels] \
  [--poetry-config/--no-poetry-config] [--poetry-root <dir>] \
  [--ui-dir <dir>] [--ui-build/--no-ui-build] [--ui-dist dist] \
  [--ui-git <url>] [--ui-ref main] [--ui-subdir <dir>] \
  [--ui-git-ssh-key <path>] [--ui-git-insecure-host] \
  [--ui-git-username <name>] [--ui-git-password <pwd>] [--ui-git-token <token>]
```

### forge pkg inspect

```bash
forge pkg inspect <package.l6e> [--show-config] [--manifest-only]
```

### forge pkg contents

```bash
forge pkg contents <package.l6e> [--tree/--no-tree] [--limit <n>] [--stats] [--artifacts]
```

### forge pkg install

```bash
forge pkg install <package.l6e> [--workspace|-w <workspace>] [--overwrite] \
  [--verify/--no-verify] [--verify-sig] [--public-key <path>] \
  [--install-wheels/--no-install-wheels] [--venv-path <path>]
```

## Memory Helpers

Collections let you target different backing stores or logical buckets in addition to namespaces. Use `--collection` (or `-c`) to override the backend default collection.

The API also accepts a `collection` field directly; the CLI passes it through as provided.

```bash
# Upsert into a namespace under the default collection
forge memory upsert --ns <namespace> --key <key> --content "text"

# Upsert into a specific collection
forge memory upsert --collection <collection> --ns <namespace> --key <key> --content "text"

# Search within a namespace
forge memory search --ns <namespace> --query "question" [--limit 5]

# Search within a specific collection + namespace
forge memory search --collection <collection> --ns <namespace> --query "question" [--limit 5]
```


