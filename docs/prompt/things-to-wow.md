### Top “wow” moments to finish next

- One-command local stack + UI
  - forge up --agents demo opens a browser chat UI wired to the agent with hot reload, traces, and tool call visualization. Auto-infers compose services, boots models (or falls back to echo), and shows live logs.

- Seamless model bootstrap
  - Auto-detect Ollama/LM Studio; if missing, offer to install or switch to echo. Pull a small chat + embedding model with progress bars and readiness checks, so the scaffolded agent responds instantly.

- Per‑agent environment bootstrap
  - forge pkg install --venv creates a per‑agent venv and installs deps (from wheelhouse when present), with health checks and “ready to run” summary.

- One-command deployable artifact
  - forge pkg image build --tag org/agent:ver to produce an OCI image with the agent + runtime, then forge stack up --image org/agent:ver to run it. Bonus: emit OpenAPI and Postman collection via forge run api.

- Registry UX (local-first)
  - forge pkg publish --to dir:///… and forge pkg install name@ver --from dir:///… with search/inspect in a simple local index, making share/install feel like a marketplace even offline.

If we do just the first two, developers will see an agent respond in a browser within minutes, with real traces and zero manual setup—that’s the “wow.”