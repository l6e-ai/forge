### Top “wow” moments to finish next

- Per‑agent environment bootstrap
  - forge pkg install --venv creates a per‑agent venv and installs deps (from wheelhouse when present), with health checks and “ready to run” summary.

- One-command deployable artifact
  - forge pkg image build --tag org/agent:ver to produce an OCI image with the agent + runtime, then forge stack up --image org/agent:ver to run it. Bonus: emit OpenAPI and Postman collection via forge run api.

- Registry UX (local-first)
  - forge pkg publish --to dir:///… and forge pkg install name@ver --from dir:///… with search/inspect in a simple local index, making share/install feel like a marketplace even offline.

If we do just the first two, developers will see an agent respond in a browser within minutes, with real traces and zero manual setup—that’s the “wow.”
