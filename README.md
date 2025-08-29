[![pytest](https://github.com/l6e-ai/forge/actions/workflows/pytest.yml/badge.svg?branch=main)](https://github.com/l6e-ai/forge/actions/workflows/pytest.yml)
[![mypy](https://github.com/l6e-ai/forge/actions/workflows/mypy.yml/badge.svg?branch=main)](https://github.com/l6e-ai/forge/actions/workflows/mypy.yml)
[![ruff](https://github.com/l6e-ai/forge/actions/workflows/ruff.yml/badge.svg?branch=main)](https://github.com/l6e-ai/forge/actions/workflows/ruff.yml)

Forge (l6e-forge) is an open source toolkit for building and shipping local-first AI agents. It provides an optional full stack—including API, monitoring, chat UI, and pluggable memory—designed to help you rapidly prototype and deploy AI agent MVPs on your laptop, then adapt and scale as your needs grow. Forge emphasizes an adapters-first, extensible architecture, enabling you to swap out components like runners, memory, and databases without lock-in or rewrites. Learn more about Forge's features on our [site](https://l6e.ai).

## Highlights

* Agents on Rails: opinionated defaults, adapters-first, no lock-in
* Optional Docker stack: API, monitor, chat UI
* Local models: supports LM Studio and Ollama, with auto model selection
* Packaging: ships as a single `.l6e` bundle, with optional UI and Python wheels for offline installs

## Prerequisites

* Python 3.13 (Poetry recommended)
* Node 18+ (only if building a UI)
* Optional: Docker (for running the stack), Ollama/LM Studio (for local LLMs)

## Installation and Quickstart

Add the core library to your project and install the CLI as a dev dependency. Then initialize a workspace, create an agent, and chat locally:

```
# Project dependency (Poetry)
poetry add l6e-forge

# Dev dependency (CLI, Poetry)
poetry add --group dev l6e-forge-cli

# Create a new workspace
poetry run forge init ./my-workspace

# Create an agent from a template
poetry run forge create agent my-agent --template assistant

# Chat locally (no stack needed)
poetry run forge chat my-agent -w ./my-workspace
```

Using uv:

```
uv add l6e-forge
uv add --dev l6e-forge-cli
uv run forge --help
```

Using pip:

```
pip install l6e-forge l6e-forge-cli
forge --help
```

See the [Getting Started guide](https://github.com/l6e-ai/forge/blob/1aa28f9787f41928d96535fccf61609ac39826bc/docs/getting-started.md) for more details.

## Usage Examples

### Model Management

Suggest models based on available VRAM/RAM and bootstrap models interactively:

```
poetry run forge models suggest --provider ollama,lmstudio --quant auto --top 5
poetry run forge models bootstrap agents/my-agent --provider-order ollama,lmstudio --interactive
```

### Memory API

Store and search agent memory via HTTP (optionally target a specific collection with `collection`):

```
# Upsert memory
curl -X POST http://localhost:8000/api/memory/upsert \
  -H 'Content-Type: application/json' \
  -d '{"namespace": "my-agent", "key": "note-1", "content": "Daisy is allergic to peanuts", "metadata": {"type": "note"}}'

# Upsert into a specific collection
curl -X POST http://localhost:8000/api/memory/upsert \
  -H 'Content-Type: application/json' \
  -d '{"collection": "my-collection", "namespace": "my-agent", "key": "note-1", "content": "Daisy is allergic to peanuts"}'

# Search memory
curl -X POST http://localhost:8000/api/memory/search \
  -H 'Content-Type: application/json' \
  -d '{"namespace": "my-agent", "query": "What is Daisy allergic to?", "limit": 5}'

# Search within a specific collection
curl -X POST http://localhost:8000/api/memory/search \
  -H 'Content-Type: application/json' \
  -d '{"collection": "my-collection", "namespace": "my-agent", "query": "What is Daisy allergic to?", "limit": 5}'
```

### Packaging

Build a portable `.l6e` bundle, optionally including a UI and Python wheels for offline installs:

```
# Build with UI from Git
poetry run forge pkg build agents/my-agent -o dist \
  --ui-git git@github.com:l6e-ai/forge.git --ui-ref main --ui-subdir site/agent-ui --ui-build --ui-dist dist

# Build with your own custom agent UI
poetry run forge pkg build agents/my-agent -o dist \
  --ui-build --ui-dir agents/my-agent/ui --ui-dist dist

# Bundle wheels for offline install
poetry run forge pkg build agents/my-agent -o dist --bundle-wheels --requirements /tmp/req.txt
```

### Running the Local Stack

Run the full stack with Docker:

```
# From the workspace directory
poetry run forge up
# API: http://localhost:8000
# Monitor: http://localhost:8321
# UI: http://localhost:8000/ui/
```

## Environment Variables

Configure compose files, monitor/API URLs, and provider endpoints:

* `AF_COMPOSE_FILE`: Path to compose file for `forge up/down`
* `AF_MONITOR_URL`: Monitor base URL
* `AF_API_URL`: API base URL (default `http://localhost:8000/api`)
* `OLLAMA_HOST`: Ollama endpoint (default `http://localhost:11434`)
* `LMSTUDIO_HOST`: LM Studio endpoint (default `http://localhost:1234/v1`)

## Scaling and Extensibility

The default Docker stack is single-user and not horizontally scalable. To scale, deploy shared providers (e.g., Qdrant, Postgres) and switch adapters in your agent configuration. The adapters-first design lets you swap runners, memory, and databases without rewriting your agent logic.

## Documentation

For full documentation, see the [docs/](https://github.com/l6e-ai/forge/tree/1aa28f9787f41928d96535fccf61609ac39826bc/docs) folder. You can generate a documentation site using MkDocs:

```
pip install mkdocs mkdocs-material
mkdocs serve -f docs/mkdocs.yml
```

## Contributing

We welcome contributions! See the [CONTRIBUTING.md](https://github.com/l6e-ai/forge/blob/1aa28f9787f41928d96535fccf61609ac39826bc/CONTRIBUTING.md) guide for details. Note: The project is in alpha; APIs and CLIs may change.

## Roadmap

Forge is in active development. Our goals include:

* Extensibility: adapters-first architecture for easy swapping of runners, memory, and databases
* Packaging: robust, portable `.l6e` bundles with UI and offline install support
* Scale-out: support for multi-user and distributed deployments
* Memory and Model Providers: improved integrations and options
* Developer Experience: streamlined CLI, better error handling, and improved documentation
* Contributor Infrastructure: more comprehensive guides and automated tests

## License

Apache 2.0

---

For more details, usage patterns, and advanced configuration, see the [Getting Started guide](https://github.com/l6e-ai/forge/blob/1aa28f9787f41928d96535fccf61609ac39826bc/docs/getting-started.md) and [CLI reference](https://github.com/l6e-ai/forge/blob/1aa28f9787f41928d96535fccf61609ac39826bc/docs/cli.md).