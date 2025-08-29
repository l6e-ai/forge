---
sidebar_position: 4
title: Installing Agents
description: Install `.l6e` packages with checksum and signature verification; optional venv wheels install.
---

<!-- Adapted from repo docs/installing-agents.md -->

Install a packaged agent from a `.l6e` file.

## Prerequisites

- Python 3.13, `l6e-forge` core library (project dependency)
- `l6e-forge-cli` installed in your development environment
- Optional: Docker (stack), Ollama (local LLMs)

## Command

```bash
forge pkg install <package.l6e> \
  [--workspace|-w <workspace>] [--overwrite] \
  [--verify/--no-verify] [--verify-sig] [--public-key <path>] \
  [--install-wheels/--no-install-wheels] [--venv-path <path>]
```

Checksum verification is enabled by default; add `--verify-sig` for Ed25519 signature checks.

## Example

```bash
forge pkg install my-agent-1.0.0.l6e --verify --verify-sig --public-key ./public.key
```


