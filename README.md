# Forge Alpha (l6e-forge)

Forge helps you build and ship local-first AI agents with an optional full stack: API, monitoring, chat UI, and pluggable memory. Ship MVPs fast on your laptop, then adapt to your stack as you scale.

## Highlights
- Agents on Rails: opinionated defaults without lock‑in (adapters-first)
- Optional Docker stack: API, monitor, chat UI; mount from your workspace
- Local models: LM Studio and Ollama supported; Auto Models with memory estimates
- Packaging: single `.l6e` bundle with UI and optional wheelhouse for offline installs

## Prerequisites
- Python 3.13 (Poetry recommended)
- Node 18+ (only if you plan to build a UI)
- Optional: Docker (to run the stack), Ollama/LM Studio (for local LLMs)

## Quickstart
```bash
# Install CLI (recommend Poetry group cli)
poetry install --only cli

# Create a new workspace
poetry run forge init ./my-workspace

# Create an agent (examples also contain agents)
# Edit agents/my-agent/agent.py as needed

# Chat locally (no stack needed)
poetry run forge chat my-agent -w ./my-workspace
```

## Models (Suggest and Bootstrap)
```bash
# Show suggested models (VRAM/RAM-aware, with memory % and installed status)
poetry run forge models suggest --provider ollama,lmstudio --quant auto --top 5

# Bootstrap interactively and update agent config
poetry run forge models bootstrap agents/my-agent \
  --provider-order ollama,lmstudio --interactive
```

Notes:
- Quant options: `auto|q4|q5|q8|mxfp4|8bit`
- GPT‑OSS 20B/120B supported (provider‑specific sizes used when available)

## Packaging
Build a portable `.l6e` bundle. You can include a web UI and Python wheels for offline install.

### UI Packaging
- From Git
```bash
poetry run forge pkg build agents/my-agent -o dist \
  --ui-git git@github.com:l6e-ai/forge.git \
  --ui-ref main --ui-subdir site/agent-ui --ui-build --ui-dist dist \
  --ui-git-ssh-key ~/.ssh/id_ed25519
```
- From Local Dir
```bash
poetry run forge pkg build agents/my-agent -o dist \
  --ui-dir /path/to/ui --ui-build --ui-dist dist
```
UI assets are embedded under `artifacts/ui/`.

### Wheel Bundling (Offline Installs)
You have two options:
- With requirements file
```bash
echo "requests==2.32.3" > /tmp/req.txt
poetry run forge pkg build agents/my-agent -o dist \
  --bundle-wheels --requirements /tmp/req.txt
```
- With Poetry project (exported requirements)
```bash
# From repo root or set --poetry-root <dir>
poetry run forge pkg build agents/my-agent -o dist \
  --bundle-wheels --poetry-config --poetry-root .
```
Wheels are embedded under `artifacts/wheels/`. The exported requirements are embedded as `artifacts/requirements.txt`.

### Inspect a Bundle
```bash
forge pkg contents dist/my-agent-0.1.0.l6e
```

## Installing a Package
```bash
# Initialize or pick a workspace
poetry run forge init ./workspace

# Install package (verifies checksums)
poetry run forge pkg install dist/my-agent-0.1.0.l6e --workspace ./workspace --verify

# Optional: install the wheel bundle into a venv
poetry run forge pkg install dist/my-agent-0.1.0.l6e --workspace ./workspace \
  --install-wheels --venv-path ./workspace/.venv_agents/my-agent
```
On install, if the package includes a UI, it’s extracted to `workspace/ui/<agent_name>`.

## Run the Local Stack (Docker)
The default compose template mounts `./ui` into the API at `/app/static/ui`.
```bash
# From the workspace
poetry run forge up
# API http://localhost:8000  Monitor http://localhost:8321  UI http://localhost:8000/ui/
```

## Scaling and Adapters
- Base Docker stack is single‑user and not horizontally scalable
- To scale: deploy shared providers (Qdrant/Postgres/etc.) and switch adapters in the agent
- Adapters-first design enables swapping runners/memory/DBs without rewrites

## Troubleshooting
- Wheels missing in bundle: ensure `--requirements` has entries or use `--poetry-config/--poetry-root`
- Git UI build prompts for auth: use `--ui-git-ssh-key` or HTTPS with `--ui-git-token`
- UI not visible: confirm files exist in `workspace/ui/<agent_name>`; `AF_UI_DIR` is `/app/static/ui` in compose
- Models suggest empty: ensure providers are running (Ollama/LM Studio) and reachable

## Contributing
PRs welcome! See `CONTRIBUTING.md`. This is an alpha; APIs and CLIs may change.
