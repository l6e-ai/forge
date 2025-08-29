# Getting Started

## Prerequisites

Forge CLI requires Python 3.13 (Poetry is recommended for dependency management). Node.js 18+ is only needed if you plan to build a UI. Optional dependencies include Docker (for running the stack) and Ollama or LM Studio (for local LLMs) \[[source](https://github.com/l6e-ai/forge/blob/9992fedf4d2bc696c97a5017490730e12843b0ff/README.md)\].

* [Ollama installation instructions](https://ollama.com/download)
* [Docker installation instructions](https://docs.docker.com/get-docker/)

## Installation

Install Forge using Poetry. Add the core library as a project dependency and the CLI as a dev dependency:

```
poetry add l6e-forge
poetry add --group dev l6e-forge-cli
```

Using uv:

```
uv add l6e-forge
uv add --dev l6e-forge-cli
```

Using pip:

```
pip install l6e-forge l6e-forge-cli
```

## Optional Dependencies

* **Ollama**: Used for running local LLMs. The Forge CLI will prompt you to install Ollama if it is not detected during model bootstrapping. See [Ollama's official guide](https://ollama.com/download).
* **Docker**: Required to run the full stack (API, monitor, UI) locally. See [Docker's official guide](https://docs.docker.com/get-docker/).

## Quick Start Workflow

### 1. Create a Workspace

Initialize a new workspace:

```
poetry run forge init ./my-workspace
cd my-workspace
```

This creates a workspace directory with a `forge.toml` configuration file and an `agents` directory \[[source](https://github.com/l6e-ai/forge/blob/9992fedf4d2bc696c97a5017490730e12843b0ff/README.md)\].

### 2. Create an Agent

Create an agent using a template. For a basic assistant:

```
poetry run forge create agent my-assistant --template=assistant
```

For an Ollama-powered agent with a specific model:

```
poetry run forge create agent my-ollama --provider=ollama --model llama3.2:3b
```

This scaffolds an agent directory under `agents/` with `agent.py`, `config.toml`, and optional `tools.py` \[[source](https://github.com/l6e-ai/forge/blob/9992fedf4d2bc696c97a5017490730e12843b0ff/docs/getting-started.md)\].

### 3. Bootstrap Models

To pull and verify models for your agent (and update its config), run:

```
poetry run forge models bootstrap agents/my-ollama --provider-order ollama,lmstudio --interactive
```

If models are missing, `forge up` (see below) will also trigger bootstrapping automatically \[[source](https://github.com/l6e-ai/forge/pull/1)\].

### 4. Spin Up the Stack

To start the API, monitor, and UI services (requires Docker):

```
poetry run forge up
```

* API: http://localhost:8000
* Monitor: http://localhost:8321
* UI: http://localhost:8000/ui/

You can also chat with your agent directly (no stack needed):

```
poetry run forge chat my-ollama -w ./my-workspace
```

### 5. Edit Agent with Custom Prompting

Open `agents/my-ollama/agent.py` in your editor. The agent's main logic lives in the `handle_message` method. To customize prompting, prepend recalled memory or any context to the prompt before sending it to the model. Example:

```
async def handle_message(self, message: Message, context: AgentContext) -> AgentResponse:
    # Recall related memory
    try:
        mm = self.runtime.get_memory_manager()
        memories = await mm.search_vectors(namespace="my-ollama", query=message.content, limit=3)
        recall = "\n".join(f"- {m.content}" for m in memories)
        await mm.store_vector(namespace="my-ollama", key=str(message.message_id), content=message.content, metadata={"role": message.role})
    except Exception:
        recall = ""
    # Prepend recalled context to the prompt
    sys_preface = f"You may use this related memory to answer:\n{recall}\n\n" if recall else ""
    prompt_msg = Message(role="user", content=sys_preface + message.content)
    manager = self.runtime.get_model_manager()
    spec = ModelSpec(model_id="llama3.2:3b", provider="ollama", model_name="llama3.2:3b", memory_requirement_gb=0.0)
    model_id = await manager.load_model(spec)
    chat = await manager.chat(model_id, [prompt_msg])
    return AgentResponse(content=chat.message.content, agent_id=self.name, response_time=0.0)
```

This pattern enables you to inject custom context or memory into the prompt sent to the LLM \[[source](https://github.com/l6e-ai/forge/blob/9992fedf4d2bc696c97a5017490730e12843b0ff/l6e_forge/cli/templates/agent_ollama_py.py)\].

## Workspace and Agent Structure

A typical workspace looks like:

```
my-workspace/
├── forge.toml
├── agents/
│   └── my-ollama/
│       ├── agent.py
│       ├── config.toml
│       └── tools.py (optional)
└── .forge/
    ├── logs/
    └── data/
```

Each agent directory contains its implementation (`agent.py`), configuration (`config.toml`), and optional tools and tests \[[source](https://github.com/l6e-ai/forge/blob/9992fedf4d2bc696c97a5017490730e12843b0ff/docs/cli-and-architecture-design.md)\].

## Best Practices

* Use Poetry for dependency management and virtual environments.
* Use Docker for running the full stack in a reproducible environment.
* Use Ollama or LM Studio for local LLMs; Forge will prompt you if they are missing.
* Edit your agent's `handle_message` method to implement custom prompting and memory recall.
* For advanced use (packaging, deployment, UI), refer to the full documentation and CLI help.

For more details, see the [Forge README](https://github.com/l6e-ai/forge/blob/9992fedf4d2bc696c97a5017490730e12843b0ff/README.md) and [Getting Started Guide](https://github.com/l6e-ai/forge/blob/9992fedf4d2bc696c97a5017490730e12843b0ff/docs/getting-started.md).
