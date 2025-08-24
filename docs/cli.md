## Forge CLI Guide

This guide documents the `forge` CLI: commands, flags, environment variables, and examples.

### Installation
```bash
poetry install --only cli
poetry run forge --help
```

### Conventions
- Replace `<workspace>` with your workspace path (contains `forge.toml` and `agents/`).
- Replace `<agent>` with your agent name (directory under `agents/`).

---

### Top-level commands

#### forge init
Create a new workspace directory with optional compose.
```bash
forge init <workspace> [--with-example] [--with-compose/--no-with-compose]
```

#### forge list
List agents in the current workspace.
```bash
forge list
```

#### forge up
Start local stack: containers (monitor, api) and dev runtime.
```bash
forge up \
  [--workspace|-w <workspace>] \
  [--compose-file|-f <path>] \
  [--monitor-url <url>] \
  [--no-dev] [--dev-only] [--build] \
  [--open-ui/--no-open-ui]
```
Notes:
- If `--dev-only` is set, containers are skipped and only the dev runtime is started.
- If `--no-dev` is set, only containers are started.
- The API is served at `http://localhost:8000`, Monitor at `http://localhost:8321`.
- UI assets, if present in `<workspace>/ui/<agent>`, are served under `http://localhost:8000/ui/`.

#### forge down
Stop the local container stack.
```bash
forge down [--compose-file|-f <path>] [--volumes|-v]
```

---

### Agent scaffolding

#### forge create agent
Create a new agent from a template and optionally generate a compose file.
```bash
forge create agent <agent> \
  [--workspace <workspace>] \
  [--provider ollama] \
  [--model llama3.2:3b] \
  [--provider-endpoint <url>] \
  [--template assistant] \
  [--include-compose/--no-include-compose] \
  [--memory-provider qdrant|memory]
```
Examples:
```bash
forge create agent my-assistant --template assistant --provider ollama --model llama3.2:3b
forge create agent my-echo --template basic --include-compose --memory-provider memory
```

#### forge template list
List available templates and supported providers.
```bash
forge template list
```

---

### Development & Chat

#### forge dev
Start dev mode (hot reload) or validate the workspace.
```bash
forge dev [--workspace|-w <workspace>] [--check]
```

#### forge chat
Chat with an agent. Supports direct-provider mode (Ollama/LM Studio) or routed runtime mode.
```bash
forge chat <agent> \
  [--message|-m "hello"] \
  [--workspace|-w <workspace>] \
  [--stream/--no-stream] \
  [--monitor-url <url>] \
  [--markdown/--no-markdown] \
  [--timeout <seconds>] \
  [--debug]
```
Examples:
```bash
forge chat my-assistant -w ./workspace
forge chat my-assistant -w ./workspace -m "Summarize our plan"
```

Direct provider mode is active when your agent config sets `agent.provider = "ollama"|"lmstudio"` and a `model`.
Use `OLLAMA_HOST` or `LMSTUDIO_HOST` to point to providers.

---

### Models

#### forge models list
List available models across providers.
```bash
forge models list [--provider ollama|lmstudio|all] [--endpoint <url>]
```

#### forge models doctor
Show system profile relevant to local model selection.
```bash
forge models doctor
```

#### forge models suggest
Show suggested chat models with estimated memory usage and fit.
```bash
forge models suggest \
  [--provider "ollama,lmstudio"] \
  [--quality speed|balanced|quality] \
  [--top <n>] \
  [--quant auto|q4|q5|q8|mxfp4|8bit]
```

#### forge models bootstrap
Interactively select and configure a model for an agent; pulls models for Ollama if needed.
```bash
forge models bootstrap <agent_dir> \
  [--provider-order "ollama,lmstudio"] \
  [--quality speed|balanced|quality] \
  [--quant auto|q4|q5|q8|mxfp4|8bit] \
  [--top <n>] \
  [--interactive/--no-interactive] \
  [--accept-best] \
  [--dry-run]
```

---

### Packaging

#### forge pkg build
Create a `.l6e` package from an agent directory. Supports bundling UI and wheels for offline installs.
```bash
forge pkg build <agent_dir> \
  [--out|-o dist] [--name <name>] [--version|-v 0.1.0] [--description <text>] \
  [--sign-key <path>] [--profile thin|medium|fat] \
  [--include-compose] [--compose-services auto|<svc1,svc2>] \
  [--requirements <req.txt>] \
  [--bundle-wheels/--no-bundle-wheels] \
  [--poetry-config/--no-poetry-config] [--poetry-root <dir>] \
  [--ui-dir <dir>] [--ui-build/--no-ui-build] [--ui-dist dist] \
  [--ui-git <url>] [--ui-ref main] [--ui-subdir <dir>] \
  [--ui-git-ssh-key <path>] [--ui-git-insecure-host] \
  [--ui-git-username <name>] [--ui-git-password <pwd>] [--ui-git-token <token>]
```

#### forge pkg inspect
Display metadata and (optionally) embedded agent config.
```bash
forge pkg inspect <package.l6e> [--show-config] [--manifest-only]
```

#### forge pkg contents
List files inside a `.l6e` and summarize artifacts.
```bash
forge pkg contents <package.l6e> [--tree/--no-tree] [--limit <n>] [--stats/--no-stats] [--artifacts/--no-artifacts]
```

#### forge pkg install
Install a package into a workspace; optional wheel install into a venv.
```bash
forge pkg install <package.l6e> \
  [--workspace|-w <workspace>] [--overwrite] \
  [--verify/--no-verify] [--verify-sig] [--public-key <path>] \
  [--install-wheels/--no-install-wheels] [--venv-path <path>]
```

---

### Memory (API helper)

These commands call the local API (`AF_API_URL`, default `http://localhost:8000`).

#### forge memory upsert
```bash
forge memory upsert --ns <namespace> --key <key> --content "text"
```

#### forge memory search
```bash
forge memory search --ns <namespace> --query "question" [--limit 5]
```

---

### Environment variables
- `AF_COMPOSE_FILE`: Path to the compose file used by `forge up/down`. If not set, the CLI searches upward for a compose file.
- `AF_MONITOR_URL`: Base URL for the monitor service; used by dev runtime and chat.
- `AF_API_URL`: Base URL for the API used by `forge memory` commands (default `http://localhost:8000`).
- `OLLAMA_HOST`: Provider endpoint for Ollama (default `http://localhost:11434`).
- `LMSTUDIO_HOST`: Provider endpoint for LM Studio (default `http://localhost:1234/v1`).

---

### Tips
- If `forge models suggest` shows no results, ensure providers are running and reachable via the env vars above.
- When packaging a UI with `--ui-git` or `--ui-dir`, assets are embedded under `artifacts/ui/` and extracted to `<workspace>/ui/<agent>` on install.


