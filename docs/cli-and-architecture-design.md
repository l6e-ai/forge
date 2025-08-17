# Agent-Forge CLI Specification & Architecture

## Core Concepts

**Agent** - A Python class that handles specific tasks, has memory, and can use tools
**Workspace** - A directory containing agents, shared configuration, and runtime state
**Runtime** - The execution environment that runs agents and manages communication
**Tools** - Reusable capabilities (file access, web browsing, code execution)

## CLI Commands

### Workspace Management
```bash
# Initialize new workspace
forge init my-workspace
cd my-workspace

# Show workspace status
forge status
# Output: 3 agents, runtime running, 2 active conversations
```

### Agent Development
```bash
# Create new agent from template
forge create my-assistant --template=personal-assistant
forge create code-reviewer --template=coder

# List available templates
forge templates
# Output: personal-assistant, coder, researcher, basic

# List agents in workspace
forge list
# Output: my-assistant (stopped), code-reviewer (running)
```

### Development Environment
```bash
# Start full development environment
forge dev
# Starts: runtime, memory services, monitoring UI
# Opens: http://localhost:8123 (monitoring dashboard)

# Run specific agent in dev mode
forge run my-assistant --dev
# Hot reloading, debug logs, breakpoint support

# Interactive chat with agent
forge chat my-assistant
# Opens interactive terminal session
```

### Testing & Debugging
```bash
# Run agent tests
forge test my-assistant
forge test --all

# Debug mode with conversation tracing
forge debug my-assistant
# Shows: thought process, tool calls, memory access

# View agent logs
forge logs my-assistant --tail
forge logs --all --since=1h
```

### Deployment & Distribution
```bash
# Package agent for distribution
forge package my-assistant
# Creates: my-assistant.forge (installable package)

# Install agent from package
forge install ./code-reviewer.forge
forge install github.com/user/awesome-agent

# Deploy to production runtime
forge deploy my-assistant --env=production
```

## How Agent-Forge Works

### 1. Workspace Structure
```
my-workspace/
├── forge.toml                   # Workspace configuration
├── agents/
│   ├── my-assistant/
│   │   ├── agent.py            # Agent implementation
│   │   ├── config.toml         # Agent configuration
│   │   ├── tools.py            # Custom tools (optional)
│   │   └── tests/              # Agent tests
│   └── code-reviewer/
├── shared/
│   ├── tools/                  # Workspace-wide tools
│   ├── memory/                 # Shared memory data
│   └── config/                 # Runtime configuration
└── .forge/                     # Runtime state (like .git)
    ├── runtime.pid
    ├── logs/
    └── data/
```

### 2. Agent Implementation
```python
# agents/my-assistant/agent.py
from agent_forge import Agent, tool

class MyAssistant(Agent):
    def __init__(self):
        super().__init__(
            name="my-assistant",
            description="Personal productivity assistant",
            model="llama3.2:8b"
        )
    
    async def handle_message(self, message: str, context: dict) -> str:
        # Agent's main logic
        if "schedule" in message.lower():
            return await self.handle_scheduling(message)
        return await self.chat(message)
    
    @tool
    async def handle_scheduling(self, request: str) -> str:
        # Custom tool for scheduling
        calendar = await self.memory.get("calendar")
        # ... scheduling logic
        return response
```

### 3. Agent Configuration
```toml
# agents/my-assistant/config.toml
[agent]
name = "my-assistant"
description = "Personal productivity assistant"
version = "1.0.0"

[model]
provider = "ollama"
model = "llama3.2:8b"
temperature = 0.7
max_tokens = 2048

[memory]
provider = "qdrant"
collection = "assistant_memory"
max_context = 10000

[tools]
enabled = ["filesystem", "web", "calendar", "email"]

[personality]
tone = "friendly"
verbosity = "medium"
proactive = true
```

### 4. Runtime Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CLI Commands  │    │  Agent Instance │    │   Tool Registry │
│                 │    │                 │    │                 │
│ forge run       │───▶│ MyAssistant()   │◀──▶│ filesystem      │
│ forge chat      │    │                 │    │ web             │
│ forge debug     │    │ handle_message()│    │ calendar        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         │              ┌─────────────────┐              │
         │              │  Orchestrator   │              │
         │              │                 │              │
         │              │ • Routing       │              │
         │              │ • Lifecycle     │              │
         │              │ • Communication │              │
         │              └─────────────────┘              │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Monitoring UI  │    │  Memory Layer   │    │  Model Manager  │
│                 │    │                 │    │                 │
│ • Conversations │    │ • Vector Store  │    │ • Ollama        │
│ • Agent State   │    │ • Graph DB      │    │ • Llamafile     │
│ • Performance   │    │ • Session State │    │ • Model Router  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 5. Development Workflow

**Step 1: Initialize**
```bash
forge init my-workspace
cd my-workspace
```

**Step 2: Create Agent**
```bash
forge create assistant --template=personal-assistant
# Scaffolds agent.py, config.toml, tests/
```

**Step 3: Develop**
```bash
forge dev
# Starts runtime, opens monitoring UI
# Edit agents/assistant/agent.py
# Changes automatically reload
```

**Step 4: Test**
```bash
forge chat assistant
# Interactive testing

forge test assistant
# Automated tests
```

**Step 5: Deploy**
```bash
forge deploy assistant
# Runs in production mode
```

## Key Design Principles

### Convention Over Configuration
- Standard project structure
- Sensible defaults for everything
- Minimal required configuration

### Hot Reloading
- Code changes immediately reflected
- No restart needed during development
- State preservation during reloads

### Composable Tools
- Standard tool interface
- Mix and match capabilities
- Easy to create custom tools

### Observable Runtime
- All agent activity logged
- Real-time monitoring dashboard
- Conversation tracing and debugging

### Portable Agents
- Agents package into distributable files
- Share via GitHub, package registries
- Import and run with single command

This creates a development experience similar to modern web frameworks - fast iteration, clear structure, powerful tooling.