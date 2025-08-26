> **Note:** This CLI is in alpha. Features, commands, options, and behaviors are subject to change. Expect instability and evolving APIs. Always consult the latest code and documentation for updates.

## Installation

Install the CLI using Poetry:

```bash
poetry install --only cli
poetry run forge --help
```
[Source](https://github.com/l6e-ai/forge/blob/a23d7609ed652edab7a9bd1d092d2effcb9f2d33/docs/cli.md)

## Workspace Structure

A workspace consists of a root directory containing `forge.toml` and an `agents/` directory. Most commands assume you are operating within a valid workspace.

## Environment Variables

Configure CLI behavior and endpoints using these environment variables:

- `AF_COMPOSE_FILE`: Path to the compose file for `forge up/down`.
- `AF_MONITOR_URL`: Base URL for the monitor service (default: `http://localhost:8321`).
- `AF_API_URL`: Base URL for the API used by memory commands (default: `http://localhost:8000`).
- `OLLAMA_HOST`: Provider endpoint for Ollama (default: `http://localhost:11434`).
- `LMSTUDIO_HOST`: Provider endpoint for LM Studio (default: `http://localhost:1234/v1`).
[Source](https://github.com/l6e-ai/forge/blob/a23d7609ed652edab7a9bd1d092d2effcb9f2d33/docs/cli.md)

## Top-Level Commands

### `forge init`
Create a new workspace directory. Optionally scaffold a sample agent and include a production compose file.

```bash
forge init <workspace> [--with-example] [--with-compose/--no-with-compose]
```

### `forge list`
List agents in the current workspace.

```bash
forge list
```

### `forge up`
Start the local stack: containers (monitor, api) and dev runtime.

```bash
forge up \
  [--workspace|-w <workspace>] \
  [--compose-file|-f <path>] \
  [--monitor-url <url>] \
  [--no-dev] [--dev-only] [--build] \
  [--open-ui/--no-open-ui]
```
- `--dev-only`: Only start dev runtime, skip containers.
- `--no-dev`: Only start containers, skip dev runtime.
- `--build`: Build images before starting containers.
- `--open-ui`: Open the UI in your browser after start.

### `forge down`
Stop the local container stack.

```bash
forge down [--compose-file|-f <path>] [--volumes|-v]
```
- `--volumes`: Remove named volumes.

## Agent Scaffolding

### `forge create agent`
Create a new agent from a template. Supports provider, model, template, memory provider, and compose file inclusion.

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
Example:
```bash
forge create agent my-assistant --template assistant --provider ollama --model llama3.2:3b
forge create agent my-echo --template basic --include-compose --memory-provider memory
```
[Source](https://github.com/l6e-ai/forge/blob/a23d7609ed652edab7a9bd1d092d2effcb9f2d33/docs/cli.md)

### `forge template list`
List available templates and supported providers.

```bash
forge template list
```

## Development & Chat

### `forge dev`
Start dev mode (hot reload) or validate the workspace.

```bash
forge dev [--workspace|-w <workspace>] [--check]
```
- `--check`: Validate workspace and exit.

### `forge chat`
Chat with an agent. Supports interactive and single-message modes, direct-provider or routed runtime.

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
- Interactive mode uses prompt history and autosuggest.
- Direct-provider mode supports streaming responses for Ollama/LM Studio.

## Model Management

### `forge models list`
List available models across providers.

```bash
forge models list [--provider ollama|lmstudio|all] [--endpoint <url>]
```

### `forge models doctor`
Show system profile relevant to local model selection.

```bash
forge models doctor
```

### `forge models suggest`
Show suggested chat models with estimated memory usage and fit.

```bash
forge models suggest \
  [--provider "ollama,lmstudio"] \
  [--quality speed|balanced|quality] \
  [--top <n>] \
  [--quant auto|q4|q5|q8|mxfp4|8bit]
```

### `forge models bootstrap`
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
[Source](https://github.com/l6e-ai/forge/blob/a23d7609ed652edab7a9bd1d092d2effcb9f2d33/docs/cli.md)

## Packaging

### `forge pkg build`
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

### `forge pkg inspect`
Display metadata and optionally embedded agent config.

```bash
forge pkg inspect <package.l6e> [--show-config] [--manifest-only]
```

### `forge pkg contents`
List files inside a `.l6e` and summarize artifacts.

```bash
forge pkg contents <package.l6e> [--tree/--no-tree] [--limit <n>] [--stats/--no-stats] [--artifacts/--no-artifacts]
```

### `forge pkg install`
Install a package into a workspace; optional wheel install into a venv.

```bash
forge pkg install <package.l6e> \
  [--workspace|-w <workspace>] [--overwrite] \
  [--verify/--no-verify] [--verify-sig] [--public-key <path>] \
  [--install-wheels/--no-install-wheels] [--venv-path <path>]
```
[Source](https://github.com/l6e-ai/forge/blob/a23d7609ed652edab7a9bd1d092d2effcb9f2d33/docs/cli.md)

## Memory API Helpers

These commands call the local API (`AF_API_URL`, default `http://localhost:8000`).

### `forge memory upsert`
Upsert memory content.

```bash
forge memory upsert --ns <namespace> --key <key> --content "text"
```

### `forge memory search`
Search memory content.

```bash
forge memory search --ns <namespace> --query "question" [--limit 5]
```
[Source](https://github.com/l6e-ai/forge/blob/a23d7609ed652edab7a9bd1d092d2effcb9f2d33/docs/cli.md)

## Tips & Caveats

- If `forge models suggest` shows no results, ensure providers are running and reachable via the relevant environment variables.
- When packaging a UI with `--ui-git` or `--ui-dir`, assets are embedded under `artifacts/ui/` and extracted to `<workspace>/ui/<agent>` on install.
- Many commands rely on external services (Ollama, LM Studio, Qdrant, Docker, Poetry, etc.) being available and correctly configured.
- Error handling uses colored output for clarity; use `--debug` for tracebacks.
- Features, options, and behaviors may change rapidly during alpha. Consult the CLI help output and codebase for the latest details.

## Best Practices

- Always validate your workspace with `forge dev --check` before starting development.
- Use environment variables to customize endpoints and compose file locations for local or containerized setups.
- Prefer interactive model selection for best fit, but use `--accept-best` or `--dry-run` for automation.
- When packaging agents, use signing and verification options for integrity, especially in collaborative or production environments.

For further details, see the [CLI source code and documentation](https://github.com/l6e-ai/forge/blob/a23d7609ed652edab7a9bd1d092d2effcb9f2d33/docs/cli.md).
