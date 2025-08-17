# Configuration Schemas & File Formats

## Workspace Configuration (`forge.toml`)

```toml
[workspace]
name = "my-ai-workspace"
version = "1.0.0"
description = "My personal AI agent workspace"

[runtime]
host = "localhost"
port = 8123
debug = true
hot_reload = true
max_concurrent_agents = 5

[memory]
# Default memory provider for all agents
provider = "qdrant"  # qdrant, chroma, memory, sqlite
host = "localhost"
port = 6333
# Optional: database credentials, connection pools, etc.

[models]
# Default model configuration
default_provider = "ollama"  # ollama, llamafile, openai, anthropic
default_model = "llama3.2:8b"
max_gpu_memory = "24GB"
model_cache_dir = "./models"

# Model-specific configurations
[models.providers.ollama]
host = "localhost"
port = 11434
timeout = 300

[models.providers.openai]
api_key_env = "OPENAI_API_KEY"
organization = "org-xyz"

[tools]
# Global tool configuration
enabled = ["filesystem", "web", "terminal"]
sandbox_mode = true
max_execution_time = 30

[tools.filesystem]
allowed_paths = ["./workspace", "./data"]
denied_paths = ["/etc", "/usr"]

[tools.web]
max_requests_per_minute = 60
allowed_domains = ["*.github.com", "*.stackoverflow.com"]

[monitoring]
enabled = true
log_level = "INFO"
metrics_retention_days = 7
conversation_retention_days = 30
```

## Agent Configuration (`agents/{name}/config.toml`)

```toml
[agent]
name = "personal-assistant"
description = "A helpful personal productivity assistant"
version = "1.0.0"
author = "Your Name <you@example.com>"
license = "MIT"

[model]
provider = "ollama"  # Overrides workspace default
model = "llama3.2:8b"
temperature = 0.7
max_tokens = 2048
context_window = 4096

# Model-specific parameters
[model.parameters]
top_p = 0.9
frequency_penalty = 0.0
presence_penalty = 0.0

[memory]
# Memory configuration for this agent
provider = "qdrant"  # Inherits from workspace if not specified
collection = "personal_assistant_memory"
embedding_model = "all-MiniLM-L6-v2"
max_context_messages = 50
memory_decay_days = 90

[tools]
# Tools this agent can use
enabled = [
    "filesystem",
    "web_search",
    "calendar",
    "email",
    "notes"
]

# Tool-specific configuration
[tools.filesystem]
allowed_paths = ["./personal", "./documents"]
read_only = false

[tools.web_search]
search_engine = "brave"  # brave, google, duckduckgo
max_results = 10

[tools.calendar]
provider = "google"  # google, outlook, ical
calendar_id = "primary"

[personality]
tone = "friendly"        # friendly, professional, casual, formal
verbosity = "medium"     # low, medium, high
proactive = true        # Suggest actions vs just respond
creativity = 0.7        # 0.0 to 1.0
humor = false

[capabilities]
# What this agent specializes in
primary = ["productivity", "scheduling", "task_management"]
secondary = ["research", "writing", "organization"]

[behavior]
# Behavioral configuration
max_conversation_turns = 100
auto_save_frequency = 5  # Save state every N messages
interrupt_handling = "graceful"  # graceful, immediate, queue

[development]
# Development-specific settings
auto_reload = true
debug_mode = true
log_thoughts = true  # Log internal reasoning
test_mode = false
```

## Tool Configuration (`tools/{name}/config.toml`)

```toml
[tool]
name = "web_search"
description = "Search the web for information"
version = "1.0.0"
category = "research"

[parameters]
# JSON Schema for tool parameters
[parameters.properties.query]
type = "string"
description = "Search query"
required = true

[parameters.properties.max_results]
type = "integer"
description = "Maximum number of results"
default = 10
minimum = 1
maximum = 50

[execution]
timeout = 30
requires_internet = true
sandbox_safe = true
rate_limit = "60/minute"

[dependencies]
# External dependencies this tool needs
python_packages = ["requests", "beautifulsoup4"]
system_commands = ["curl"]
environment_variables = ["SEARCH_API_KEY"]
```

## Agent Implementation Template

```python
# agents/personal-assistant/agent.py
from agent_forge import Agent, tool, config
from agent_forge.types import Message, AgentContext, AgentResponse
from typing import Dict, List, Any

@config.load_from_file("config.toml")
class PersonalAssistant(Agent):
    """Personal productivity assistant agent"""
    
    def __init__(self):
        # Config is automatically loaded from config.toml
        super().__init__()
        
        # Agent-specific initialization
        self.task_list = []
        self.calendar_cache = {}
    
    async def handle_message(self, message: Message, context: AgentContext) -> AgentResponse:
        """Main message router"""
        content = message.content.lower()
        
        # Intent detection and routing
        if self._is_scheduling_request(content):
            return await self._handle_scheduling(message, context)
        elif self._is_task_request(content):
            return await self._handle_tasks(message, context)
        elif self._is_research_request(content):
            return await self._handle_research(message, context)
        else:
            return await self._handle_general_chat(message, context)
    
    def _is_scheduling_request(self, content: str) -> bool:
        keywords = ["schedule", "calendar", "meeting", "appointment", "book"]
        return any(keyword in content for keyword in keywords)
    
    @tool(
        description="Manage calendar and scheduling",
        parameters={
            "action": {"type": "string", "enum": ["view", "add", "update", "delete"]},
            "event_details": {"type": "object", "required": ["title", "date"]}
        }
    )
    async def manage_calendar(self, action: str, event_details: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Calendar management tool"""
        # Implementation here
        pass
    
    @tool(description="Search the web for information")
    async def web_search(self, query: str, max_results: int = 10, context: AgentContext) -> List[Dict[str, Any]]:
        """Web search tool"""
        # Implementation here
        pass

# Export the agent class for the runtime to discover
__all__ = ["PersonalAssistant"]
```

## Template Definitions (`templates/{name}/template.toml`)

```toml
[template]
name = "personal-assistant"
description = "A productivity-focused personal assistant"
version = "1.0.0"
category = "productivity"
difficulty = "beginner"  # beginner, intermediate, advanced

[files]
# Files to generate from this template
agent_file = "agent.py"
config_file = "config.toml"
tests_file = "tests/test_agent.py"
readme_file = "README.md"

[variables]
# Template variables with defaults
[variables.agent_name]
description = "Name of the agent"
type = "string"
default = "my-assistant"

[variables.description]
description = "Agent description"
type = "string"
default = "A helpful assistant"

[variables.model]
description = "Default model to use"
type = "string"
default = "llama3.2:8b"
choices = ["llama3.2:8b", "llama3.2:70b", "mixtral:8x7b"]

[variables.tools]
description = "Tools to enable"
type = "array"
default = ["filesystem", "web"]
choices = ["filesystem", "web", "terminal", "calendar", "email"]

[dependencies]
# What this template requires
python_packages = ["aiohttp", "pydantic"]
system_requirements = ["git"]
minimum_memory = "8GB"
```

## Development Environment (`docker-compose.yml`)

```yaml
version: '3.8'

services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - ./data/qdrant:/qdrant/storage

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ./data/ollama:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - ./data/redis:/data

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: forge
      POSTGRES_USER: forge
      POSTGRES_PASSWORD: forge123
    ports:
      - "5432:5432"
    volumes:
      - ./data/postgres:/var/lib/postgresql/data

  agent-forge:
    build: .
    ports:
      - "8123:8123"
    volumes:
      - .:/workspace
    environment:
      - FORGE_WORKSPACE=/workspace
      - FORGE_ENV=development
    depends_on:
      - qdrant
      - ollama
      - redis
      - postgres
```

## Key Design Decisions

### Configuration Hierarchy
1. **Workspace defaults** in `forge.toml`
2. **Agent overrides** in `agents/{name}/config.toml`  
3. **Runtime overrides** via environment variables
4. **CLI overrides** via command-line flags

### Template System
- **Jinja2-based** templating for file generation
- **Variable prompting** during `forge create`
- **Dependency checking** to ensure requirements are met
- **Multi-file templates** for complex agent types

### Development vs Production
- **Development**: Hot reloading, debug logging, monitoring UI
- **Production**: Optimized models, minimal logging, health checks
- **Environment detection** via `FORGE_ENV` variable

This configuration system gives developers:
- **Sensible defaults** with easy customization
- **Type safety** via schema validation
- **Environment flexibility** dev → staging → production
- **Template consistency** across agent types