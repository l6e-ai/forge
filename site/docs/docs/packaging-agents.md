---
sidebar_position: 3
title: Packaging Agents
---

<!-- Adapted from repo docs/packaging-agents.md -->

The `forge pkg build` command creates a `.l6e` package from an agent directory.

## Basic Usage

```bash
forge pkg build /path/to/agent --out dist --name myagent --version 1.0.0 \
  --description "My agent description"
```

## Options

- Output/profile: `--out`, `--profile thin|medium|fat`
- Compose overlay: `--include-compose`, `--compose-services auto|svc1,svc2`
- Wheels: `--requirements`, `--bundle-wheels`, `--poetry-config`, `--poetry-root`
- UI: `--ui-dir`, `--ui-build`, `--ui-dist`, `--ui-git`, `--ui-ref`, `--ui-subdir`,
  `--ui-git-ssh-key`, `--ui-git-insecure-host`, `--ui-git-username`, `--ui-git-password`, `--ui-git-token`
- Signing: `--sign-key <path>` (Ed25519)

## Examples

Bundle dependencies as wheels:

```bash
forge pkg build ./agent --bundle-wheels --requirements ./requirements.txt
```

Include UI from git:

```bash
forge pkg build ./agent --ui-git https://github.com/example/ui.git --ui-build --ui-dist dist
```

Compose overlay and signature:

```bash
forge pkg build ./agent --include-compose --sign-key ./ed25519_private.key
```


