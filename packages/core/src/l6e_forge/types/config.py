# l6e_forge/types/config.py
"""Configuration types for l6e-forge system"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Literal
from pathlib import Path

# ============================================================================
# Core Configuration Types
# ============================================================================


@dataclass
class WorkspaceInfo:
    """Basic workspace information"""

    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""


@dataclass
class RuntimeConfig:
    """Runtime system configuration"""

    host: str = "localhost"
    port: int = 8123
    debug: bool = True
    hot_reload: bool = True

    # Resource limits
    max_concurrent_agents: int = 5
    max_memory_per_agent_gb: float = 8.0
    max_execution_time: int = 300

    # Performance
    worker_threads: int = 4
    queue_size: int = 1000


@dataclass
class MemoryConfig:
    """Memory system configuration"""

    provider: Literal["qdrant", "chroma", "memory", "sqlite"] = "memory"

    # Connection settings
    host: str = "localhost"
    port: int = 6333

    # Memory behavior
    collection: Optional[str] = None
    embedding_model: str = "nomic-embed-text:latest"
    max_context_messages: int = 50
    memory_decay_days: int = 90

    # Performance settings
    batch_size: int = 100
    max_connections: int = 10

    # Provider-specific settings
    provider_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelsConfig:
    """Model system configuration"""

    default_provider: str = "ollama"
    default_model: str = "llama3.2:8b"
    max_gpu_memory: str = "24GB"
    model_cache_dir: Path = Path("./models")

    # Provider configurations
    providers: Dict[str, Dict[str, Any]] = field(default_factory=dict)


@dataclass
class ToolsConfig:
    """Tool configuration for agents"""

    enabled: List[str] = field(default_factory=list)

    # Security settings
    sandbox_mode: bool = True
    max_execution_time: int = 30

    # Tool-specific configurations
    tool_configs: Dict[str, Dict[str, Any]] = field(default_factory=dict)


@dataclass
class MonitoringConfig:
    """Monitoring and logging configuration"""

    enabled: bool = True
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # Retention
    metrics_retention_days: int = 7
    conversation_retention_days: int = 30
    log_retention_days: int = 14

    # Features
    enable_tracing: bool = False
    enable_profiling: bool = False


@dataclass
class WorkspaceConfig:
    """Complete workspace configuration"""

    workspace: WorkspaceInfo
    runtime: RuntimeConfig
    memory: MemoryConfig
    models: ModelsConfig
    tools: ToolsConfig
    monitoring: MonitoringConfig


# ============================================================================
# Agent Configuration Types
# ============================================================================


@dataclass
class ModelConfig:
    """Model configuration for agents"""

    provider: Literal["ollama", "llamafile", "openai", "anthropic"] = "ollama"
    model: str = "llama3.2:8b"

    # Generation parameters
    temperature: float = 0.7
    max_tokens: int = 2048
    context_window: int = 4096

    # Advanced parameters
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: List[str] = field(default_factory=list)

    # Provider-specific settings
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PersonalityConfig:
    """Agent personality and communication style"""

    tone: Literal["friendly", "professional", "casual", "formal"] = "friendly"
    verbosity: Literal["low", "medium", "high"] = "medium"
    proactive: bool = True
    creativity: float = 0.7  # 0.0 to 1.0
    humor: bool = False
    formality: float = 0.5
    empathy: float = 0.8


@dataclass
class CapabilitiesConfig:
    """Agent capabilities and specializations"""

    primary: List[str] = field(default_factory=list)
    secondary: List[str] = field(default_factory=list)

    # Capability metadata
    expertise_level: Dict[str, Literal["beginner", "intermediate", "expert"]] = field(
        default_factory=dict
    )
    confidence_threshold: float = 0.7


@dataclass
class BehaviorConfig:
    """Agent behavioral settings"""

    max_conversation_turns: int = 100
    auto_save_frequency: int = 5
    interrupt_handling: Literal["graceful", "immediate", "queue"] = "graceful"

    # Response behavior
    response_timeout: int = 30
    max_retries: int = 3
    fallback_behavior: Literal["error", "default_response", "escalate"] = "error"


@dataclass
class DevelopmentConfig:
    """Development-specific settings"""

    auto_reload: bool = True
    debug_mode: bool = True
    log_thoughts: bool = True
    test_mode: bool = False

    # Development tools
    enable_profiling: bool = False
    enable_tracing: bool = False


@dataclass
class AgentInfo:
    """Basic agent information"""

    name: str
    description: str
    version: str = "1.0.0"
    author: str = ""
    license: str = "Apache 2.0"


@dataclass
class AgentConfig:
    """Complete agent configuration"""

    # Core identity
    agent: AgentInfo

    # System configuration
    model: ModelConfig
    memory: MemoryConfig
    tools: ToolsConfig

    # Behavioral configuration
    personality: PersonalityConfig
    capabilities: CapabilitiesConfig
    behavior: BehaviorConfig

    # Development configuration
    development: DevelopmentConfig


# ============================================================================
# Security and Environment Configuration
# ============================================================================


@dataclass
class SandboxConfig:
    """Sandbox security configuration"""

    enabled: bool = True
    mode: Literal["strict", "moderate", "permissive"] = "moderate"

    # File system restrictions
    allowed_read_paths: List[Path] = field(default_factory=list)
    allowed_write_paths: List[Path] = field(default_factory=list)
    denied_paths: List[Path] = field(default_factory=list)

    # Network restrictions
    allow_network: bool = False
    allowed_domains: List[str] = field(default_factory=list)
    allowed_ports: List[int] = field(default_factory=list)

    # Process restrictions
    max_processes: int = 5
    max_execution_time: int = 30
    max_memory_mb: int = 512
    max_cpu_percent: float = 50.0

    # System call restrictions
    allowed_syscalls: List[str] = field(default_factory=list)
    denied_syscalls: List[str] = field(default_factory=list)


@dataclass
class PermissionConfig:
    """Agent permission system"""

    # Tool permissions
    tool_permissions: Dict[str, List[str]] = field(
        default_factory=dict
    )  # agent -> tools

    # Resource permissions
    max_memory_per_agent: Dict[str, int] = field(default_factory=dict)  # agent -> MB
    max_cpu_per_agent: Dict[str, float] = field(
        default_factory=dict
    )  # agent -> percentage

    # Data access permissions
    data_access_levels: Dict[str, Literal["read", "write", "admin"]] = field(
        default_factory=dict
    )

    # Inter-agent communication
    communication_matrix: Dict[str, List[str]] = field(
        default_factory=dict
    )  # agent -> can_talk_to


@dataclass
class EnvironmentConfig:
    """Environment-specific configuration"""

    environment: Literal["development", "staging", "production"]

    # Environment-specific overrides
    config_overrides: Dict[str, Any] = field(default_factory=dict)

    # Environment variables
    required_env_vars: List[str] = field(default_factory=list)
    optional_env_vars: Dict[str, str] = field(
        default_factory=dict
    )  # name -> default_value

    # Feature flags
    feature_flags: Dict[str, bool] = field(default_factory=dict)

    # External services
    external_services: Dict[str, str] = field(
        default_factory=dict
    )  # service -> endpoint


# ============================================================================
# Advanced Configuration Types
# ============================================================================


@dataclass
class MetricsConfig:
    """Metrics collection configuration"""

    enabled: bool = True
    collection_interval: int = 30  # seconds

    # Metric types to collect
    collect_performance_metrics: bool = True
    collect_resource_metrics: bool = True
    collect_business_metrics: bool = True

    # Storage
    storage_backend: Literal["memory", "prometheus", "influxdb"] = "memory"
    retention_period: int = 7  # days

    # Alerting
    enable_alerting: bool = False
    alert_thresholds: Dict[str, float] = field(default_factory=dict)


@dataclass
class TracingConfig:
    """Distributed tracing configuration"""

    enabled: bool = False
    tracer: Literal["jaeger", "zipkin", "datadog"] = "jaeger"

    # Sampling
    sampling_rate: float = 0.1  # 10%

    # Trace what
    trace_agent_calls: bool = True
    trace_tool_calls: bool = True
    trace_model_calls: bool = True
    trace_memory_operations: bool = False


# ============================================================================
# Export all configuration types
# ============================================================================

__all__ = [
    # Workspace configuration
    "WorkspaceInfo",
    "WorkspaceConfig",
    "RuntimeConfig",
    "ModelsConfig",
    "MonitoringConfig",
    # Agent configuration
    "AgentInfo",
    "AgentConfig",
    "ModelConfig",
    "PersonalityConfig",
    "CapabilitiesConfig",
    "BehaviorConfig",
    "DevelopmentConfig",
    # System configuration
    "MemoryConfig",
    "ToolsConfig",
    # Security and environment
    "SandboxConfig",
    "PermissionConfig",
    "EnvironmentConfig",
    # Advanced configuration
    "MetricsConfig",
    "TracingConfig",
]
