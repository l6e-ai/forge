# Agents on Rails
## Out of the box agent-stack with no lock-in

Forge provides an out-of-the-box stack for developing, testing, and shipping AI agents. The stack includes an API, monitoring tools, vector memory and search, conversation and message storage, and a full-stack chat interface, all designed to accelerate agent development and iteration. The architecture is adapters-first and extensible, allowing you to swap out components like runners, memory, and databases without rewriting your agent logic. This enables rapid prototyping and deployment of agent MVPs locally, with the flexibility to scale as your needs grow.

As a developer, you benefit from integrated vector memory and search via a memory API, which lets you store and query agent memory through HTTP endpoints. Monitoring and message storage are built in, and the chat UI allows you to interact with agents, test their performance, and observe their behavior in real time. The stack supports local models such as LM Studio and Ollama, with automatic model selection based on your system profile and agent configuration.

Hot reloads are enabled by default through volume mounts and optimized reloads in the Docker-based development environment. When you save a file, your agent reloads automatically, and your next message will use the updated code. This workflow minimizes friction and maximizes iteration speed during development.

Forge is designed for minimal overhead. You can ship an MVP agent in less than a day, run fully local and offline versions, or plug into cloud providers and scale globally. The default Docker stack is single-user and not horizontally scalable, but you can deploy shared providers like Qdrant and Postgres and switch adapters in your agent configuration to support cloud scaling.

To package your agents for deployment, Forge supports building portable `.l6e` bundles, optionally including a UI and Python wheels for offline installs. You can also ship a Docker Compose file with your packaged agents to orchestrate the full stack and its dependencies. Environment variables such as `AF_COMPOSE_FILE` allow you to specify the compose file for running the stack. For detailed packaging instructions, refer to the [README for packaging agents](https://github.com/l6e-ai/forge/blob/main/docs/packaging-agents.md).

Example: Running the full stack locally with Docker

```
# From your workspace directory
poetry run forge up
# API: http://localhost:8000
# Monitor: http://localhost:8321
# UI: http://localhost:8000/ui/
```

Example: Using the memory API

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

For more information on packaging agents and shipping with Compose files, see the [packaging guide](https://github.com/l6e-ai/forge/blob/main/site/l6e/README.md).