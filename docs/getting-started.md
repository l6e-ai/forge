# Getting Started (Forge Alpha)

This guide shows how to create an agent, use memory (store/search), and run locally.

## Create a Workspace and Agent
```bash
poetry run forge init ./workspace
# Use a template (basic assistant or Ollama-powered)
poetry run forge create agent my-assistant --template=assistant
# or
poetry run forge create agent my-ollama --template=ollama --model llama3.2:3b
```

Templates now:
- upsert user messages into memory
- retrieve top‑k related memories and include them as context

## Chat Locally
```bash
poetry run forge chat my-assistant -w ./workspace
```

## Memory via API (MVP)
The API exposes memory upsert and search.

- Upsert a memory entry
```bash
curl -X POST http://localhost:8000/api/memory/upsert \
  -H 'Content-Type: application/json' \
  -d '{
    "namespace": "my-assistant",
    "key": "note-1",
    "content": "Daisy is allergic to peanuts",
    "metadata": {"type": "note"}
  }'
```

- Search for related memories
```bash
curl -X POST http://localhost:8000/api/memory/search \
  -H 'Content-Type: application/json' \
  -d '{
    "namespace": "my-assistant",
    "query": "What is Daisy allergic to?",
    "limit": 5
  }'
```

## How Templates Use Memory
- On each user message, templates:
  - search: `mm.search_vectors(namespace=<agent_name>, query=<message>, limit=3)`
  - upsert: `mm.store_vector(namespace=<agent_name>, key=<message_id>, content=<message>)`
- The recalled results are appended to the prompt/response to ground the agent.

## Run the Stack (Optional)
```bash
cd ./workspace
poetry run forge up
# API: http://localhost:8000
# Monitor: http://localhost:8321
# UI: http://localhost:8000/ui/
```

## Packaging with UI and Wheels (Optional)
```bash
# Build a UI into the package (from git)
poetry run forge pkg build agents/my-assistant -o dist \
  --ui-git git@github.com:l6e-ai/forge.git --ui-ref main --ui-subdir site/agent-ui --ui-build --ui-dist dist

# Bundle wheels for offline install (requirements or Poetry)
poetry run forge pkg build agents/my-assistant -o dist \
  --bundle-wheels --requirements agents/my-assistant/requirements.txt
# or
poetry run forge pkg build agents/my-assistant -o dist \
  --bundle-wheels --poetry-config --poetry-root .
```

## Install a Package
```bash
poetry run forge pkg install dist/my-assistant-0.1.0.l6e --workspace ./workspace --verify \
  --install-wheels --venv-path ./workspace/.venv_agents/my-assistant
```

## Notes
- Embeddings are provided by Ollama or LM Studio when available; a mock is used as fallback.
- The default in-memory store is for development; switch to external stores (e.g., Qdrant) as you scale.
