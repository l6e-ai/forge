## l6e-forge: System Context Prompt

Use this document as the top-level context for contributors and assistants working on the l6e-forge repository. It describes what the project is, our north stars, scope, constraints, and how to make changes that move us forward. Paste this as a system/development prompt when engaging an LLM.

### Mission
Build the fastest, most developer-friendly way to create, run, and share local AI agents. Deliver an app‑store‑like experience for agents that run entirely on the developer's machine.

### North Stars
- **App-store experience for agents**: Discover, install, run, and share agents as easily as apps.
- **Local-first and private**: Agents run locally by default, with zero required cloud dependencies.
- **Developer speed**: File save → hot reload → test change in seconds.
- **Template-driven onboarding**: From install to working agent in under 5 minutes.

### Current Status (Repo Snapshot)
- Types and interfaces are in place: `l6e_forge/types/*`, `l6e_forge/core/agents/base.py`, `l6e_forge/runtime/base.py`.
- CLI foundation implemented: `forge init`, `forge create`, `forge dev`, `forge chat`, `forge template list`, `forge models list`.
- Minimal runtime working: `LocalRuntime` registers agents, passes runtime into agents, and dev hot‑reload re‑registers agents with debounce.
- Templates: Jinja2 engine with provider‑pluggable assistant templates (Ollama, LM Studio) and basic echo.
- Model managers: Ollama + LM Studio (OpenAI‑compatible) with basic health/list endpoints.
- Config manager: loads TOML (`forge.toml`, per‑agent `config.toml`), with precedence (CLI > agent > workspace) used in chat/dev.
- Minimal `pyproject.toml` (Python >= 3.13), docs skeleton under `docs/`.

### MVP Scope (Phase 1-2)
- **CLI foundation**: `forge init`, `forge create`, `forge dev`, `forge chat`, `forge list`.
- **Agent base class**: Simple `handle_message()` with tool access.
- **Hot reload**: Watch agent files and reload within ~1s, preserving context when possible.
- **Ollama only**: Local model integration to keep footprint minimal.
- **Essential tools**: Filesystem, web requests, terminal (safe/sandboxed).
- **Basic memory**: In-memory + SQLite persistence.
- **Templates**: `basic`, `assistant`, `coder` to accelerate onboarding.

### Post-MVP (Direction, not required now)
- Packaging and distribution: `.forge` package format; install from local path or Git URL.
- Monitoring UI: Local web dashboard (FastAPI + WebSocket) for conversations, errors, metrics.
- Registry/marketplace: Agent discovery and sharing.
- Advanced memory, multiple model providers, richer security sandboxing.

### Target Developer Workflow
1) Install → `forge init my-workspace` → `forge create assistant` → `forge dev`
2) Edit agent → save → hot reload
3) `forge chat assistant` for interactive testing
4) Later: `forge package`, `forge install`, `forge deploy`

### CLI Command Specs (MVP)
- **forge init <workspace>**: Create workspace structure and default `forge.toml`.
- **forge create <agent> [--template=<name>]**: Scaffold agent folder with `agent.py`, `config.toml`, optional `tools.py`.
- **forge list**: List agents in the current workspace and their status.
- **forge dev**: Start local runtime, hot reload, and monitoring hooks (UI later).
- **forge chat <agent>**: Open interactive REPL with the agent; uses agent/workspace config by default.
- **forge template list**: List available templates and supported providers.
- **forge models list [--provider]**: List models from local providers (Ollama, LM Studio).

### Architecture Overview
- **CLI** (`l6e_forge/cli/`): Typer-based commands (`create`, `dev`, `chat`, `template`, `models`).
- **Core/Agents** (`l6e_forge/core/agents/`): `IAgent` protocol; base agent contract.
- **Runtime** (`l6e_forge/runtime/`): `IRuntime` protocol; `local.py` implementation with hot reload + registration.
- **Models** (`l6e_forge/models/managers/`): Model managers; implemented: `ollama.py`, `lmstudio.py`.
- **Templates** (`l6e_forge/cli/templates/*`, `l6e_forge/workspace/template_engine/`): Jinja2 engine; provider-pluggable assistant/echo templates.
- **Tools** (`l6e_forge/tools/`): Filesystem, web, terminal + `registry` for discovery/permissions.
- **Memory** (`l6e_forge/memory/`): In-memory + SQLite managers.
- **Events/Monitoring** (`l6e_forge/events/*`, `l6e_forge/runtime/monitoring.py`): Event bus hooks; UI arrives post‑MVP.

### Design Principles
- **Convention over configuration**: Standard workspace layout; sensible defaults.
- **Simple first**: Implement the shortest path to “chat with a scaffolded agent”.
- **Observability**: Log everything relevant to dev experience; actionable errors.
- **Typed Python**: Strong typing, explicit public APIs, clear naming.

### Quality Bar (MVP DoD)
- Works on clean macOS with Python 3.13+.
- From `forge init` to first `forge chat` response in < 5 minutes.
- Hot reload reflects changes in < 1 second.
- Helpful, actionable error messages and docs quickstart.

### Implementation Preferences
- Python 3.13+, MIT license.
- Libraries: `typer`, `rich`, `watchdog`, `httpx`, `sqlite3`/`aiosqlite`, `tomllib`/`tomli`.
- Keep dependencies minimal; defer complex features until post‑MVP.
- Favor clear, verbose, well-typed code over cleverness.

### Remaining MVP Work (Gaps to close)
- **Runtime/config cohesion**:
  - Honor `models.endpoints.*` in `LocalRuntime.get_model_manager()`; add a provider registry instead of hardcoding.
  - Persist agent path → agent ID mapping for robust reloads.
- **Config UX**:
  - Add schema validation and helpful errors for `forge.toml` and per‑agent `config.toml`.
  - Show provider/model and status in `forge list` by reading agent config.
- **CLI polish**:
  - `forge dev` expose `--debounce` and reflect effective config in startup banner.
  - Improve error messages and troubleshooting hints (e.g., provider offline, model missing).
- **Chat UX**:
  - Optional streaming output; richer REPL controls (multiline send with Shift+Enter).
- **Testing/CI**:
  - Add provider‑mocked tests for `forge chat` provider path and `forge models list`.
  - Set up CI to run `poetry run pytest` on PRs.
- **Docs**:
  - Quickstart from `forge init` → `forge create` (assistant with Ollama/LM Studio) → `forge dev` → `forge chat`.
  - Troubleshooting for local providers/endpoints and model pulls.

### Assistant Working Agreement (when using this prompt)
- Prioritize the MVP commands and hot reload path before extras.
- When making code edits:
  - Add necessary imports and keep code runnable end‑to‑end.
  - Maintain existing indentation style and formatting; match file conventions.
  - Prefer small, focused edits; avoid refactors outside the task.
  - Ensure type safety and avoid introducing linter errors.
- For CLI work, use `typer` and provide helpful `--help` text.
- For file watching, use `watchdog` with efficient path filters.
- For Ollama, provide clear error messages and model installation hints.
- Default to local‑only behavior; no network unless explicitly required.

### Workspace Conventions
- Workspace structure under a user project (created by `forge init`):
```
my-workspace/
├── forge.toml
├── agents/
│   └── <agent-name>/
│       ├── agent.py
│       ├── config.toml
│       └── tools.py (optional)
└── .forge/
    ├── logs/
    └── data/
```

### Open Questions (Track, don’t block MVP)
- Exact `.forge` package format and signing.
- Monitoring UI timing (phase vs post‑MVP).
- Tool sandbox policies and permission prompts.
- Conversation history persistence format.

### Success Metrics
- Developer experience: time to first agent, hot reload speed, first chat latency.
- Technical: memory usage bounds during dev, stability in the dev loop.
- Adoption: working examples and clear docs.

If in doubt, choose the path that shortens time‑to‑first‑chat and improves the local developer workflow. The “app‑store” experience is our north star; the MVP proves it locally with fast scaffolding, hot reload, and a smooth chat loop.


