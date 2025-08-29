# l6e_forge/types/tool.py
"""Tool system types for l6e-forge"""

from dataclasses import dataclass, field
from typing import Any, Literal
from datetime import datetime
from pathlib import Path
import uuid

# ============================================================================
# Core Tool Types
# ============================================================================


@dataclass
class ToolSpec:
    """Tool specification and metadata"""

    name: str
    description: str
    category: str
    version: str = "1.0.0"

    # Parameters (JSON Schema)
    parameters_schema: dict[str, Any] = field(default_factory=dict)
    return_schema: dict[str, Any] = field(default_factory=dict)

    # Execution info
    execution_time_estimate: float = 1.0  # seconds
    requires_internet: bool = False
    sandbox_safe: bool = True

    # Dependencies
    python_packages: list[str] = field(default_factory=list)
    system_commands: list[str] = field(default_factory=list)
    environment_variables: list[str] = field(default_factory=list)

    # Resource requirements
    max_memory_mb: int = 512
    max_execution_time: int = 30
    max_cpu_percent: float = 50.0

    # Metadata
    author: str = ""
    license: str = "Apache 2.0"
    tags: list[str] = field(default_factory=list)
    homepage: str = ""

    # Capabilities
    supports_streaming: bool = False
    supports_cancellation: bool = True
    idempotent: bool = True


@dataclass
class ToolContext:
    """Context provided to tool during execution"""

    agent_id: str
    conversation_id: str  # Keep as string for tool-facing context/JSON boundaries
    session_id: str

    # Execution environment
    workspace_path: Path
    temp_dir: Path

    # Security context
    allowed_paths: list[Path] = field(default_factory=list)
    denied_paths: list[Path] = field(default_factory=list)

    # Resource limits
    max_execution_time: int = 30
    max_memory_mb: int = 512
    max_output_size: int = 1024 * 1024  # 1MB

    # Network restrictions
    allow_network: bool = False
    allowed_domains: list[str] = field(default_factory=list)
    allowed_ports: list[int] = field(default_factory=list)

    # User context
    user_id: str | None = None
    user_preferences: dict[str, Any] = field(default_factory=dict)

    # Tool context
    tool_config: dict[str, Any] = field(default_factory=dict)
    shared_state: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolCall:
    """Record of a tool being called"""

    tool_id: str
    parameters: dict[str, Any]

    # Execution info
    call_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)

    # Results
    result: Any = None
    execution_time: float = 0.0
    success: bool = False
    error_message: str | None = None

    # Context
    agent_id: str = ""
    conversation_id: str = ""

    # Resource usage
    memory_used_mb: float = 0.0
    cpu_time_seconds: float = 0.0
    network_requests: int = 0

    # Tool metadata
    tool_version: str = ""
    retries: int = 0


@dataclass
class ToolResult:
    """Result from tool execution"""

    success: bool
    data: Any = None
    error_message: str | None = None

    # Execution info
    execution_time: float = 0.0
    memory_used: int = 0
    output_size: int = 0

    # Result metadata
    metadata: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    # Streaming support
    is_partial: bool = False
    stream_id: str | None = None

    # Tool output artifacts
    files_created: list[Path] = field(default_factory=list)
    files_modified: list[Path] = field(default_factory=list)


# ============================================================================
# Tool Registration and Discovery
# ============================================================================


@dataclass
class ToolRegistration:
    """Tool registration record"""

    tool_id: str
    spec: ToolSpec

    # Registration info
    registered_at: datetime = field(default_factory=datetime.now)
    registered_by: str | None = None

    # Runtime info
    instance_count: int = 0
    total_calls: int = 0
    successful_calls: int = 0

    # Health status
    is_available: bool = True
    last_health_check: datetime = field(default_factory=datetime.now)
    health_score: float = 1.0

    # Performance metrics
    avg_execution_time: float = 0.0
    success_rate: float = 1.0


@dataclass
class ToolCategory:
    """Tool category definition"""

    name: str
    description: str

    # Category metadata
    parent_category: str | None = None
    subcategories: list[str] = field(default_factory=list)

    # Category tools
    tool_count: int = 0
    popular_tools: list[str] = field(default_factory=list)

    # Category settings
    default_permissions: list[str] = field(default_factory=list)
    security_level: Literal["low", "medium", "high"] = "medium"


# ============================================================================
# Tool Execution Types
# ============================================================================


@dataclass
class ToolExecutionRequest:
    """Request to execute a tool"""

    tool_id: str
    parameters: dict[str, Any]
    context: ToolContext

    # Execution options
    timeout: int | None = None
    priority: int = 5  # 1-10, lower = higher priority
    async_execution: bool = False

    # Request metadata
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    requested_by: str = ""
    requested_at: datetime = field(default_factory=datetime.now)


@dataclass
class ToolExecutionStatus:
    """Status of tool execution"""

    request_id: str
    tool_id: str
    status: Literal["queued", "running", "completed", "failed", "cancelled"]

    # Progress info
    progress_percent: float = 0.0
    progress_message: str = ""

    # Timing
    queued_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None

    # Results (when completed)
    result: ToolResult | None = None

    # Resource usage
    current_memory_mb: float = 0.0
    peak_memory_mb: float = 0.0


@dataclass
class ToolExecutionLog:
    """Log entry for tool execution"""

    log_id: str
    request_id: str
    tool_id: str

    # Log details
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"]
    message: str
    timestamp: datetime = field(default_factory=datetime.now)

    # Context
    step: str | None = None
    data: dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Tool Security Types
# ============================================================================


@dataclass
class ToolPermission:
    """Permission for tool usage"""

    permission_id: str
    tool_id: str
    agent_id: str

    # Permission details
    allowed_operations: list[str] = field(default_factory=list)
    parameter_restrictions: dict[str, Any] = field(default_factory=dict)

    # Resource limits
    max_executions_per_hour: int = 100
    max_execution_time: int = 30
    max_memory_mb: int = 512

    # Granted info
    granted_by: str = ""
    granted_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime | None = None

    # Usage tracking
    usage_count: int = 0
    last_used: datetime | None = None


@dataclass
class ToolAuditLog:
    """Audit log for tool usage"""

    audit_id: str
    tool_id: str
    agent_id: str

    # Action details
    action: Literal[
        "execute", "register", "unregister", "permission_grant", "permission_revoke"
    ]
    parameters: dict[str, Any] = field(default_factory=dict)

    # Results
    success: bool = True
    error_message: str | None = None

    # Context
    user_id: str | None = None
    session_id: str | None = None
    ip_address: str | None = None

    # Timing
    timestamp: datetime = field(default_factory=datetime.now)


# ============================================================================
# Tool Analytics Types
# ============================================================================


@dataclass
class ToolUsageStats:
    """Usage statistics for a tool"""

    tool_id: str

    # Usage counts
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0

    # Performance metrics
    avg_execution_time: float = 0.0
    min_execution_time: float = 0.0
    max_execution_time: float = 0.0
    p95_execution_time: float = 0.0

    # Resource usage
    avg_memory_usage: float = 0.0
    peak_memory_usage: float = 0.0
    total_cpu_time: float = 0.0

    # User patterns
    unique_agents: int = 0
    most_common_parameters: dict[str, int] = field(default_factory=dict)

    # Error analysis
    common_errors: dict[str, int] = field(default_factory=dict)
    error_rate: float = 0.0

    # Time period
    period_start: datetime = field(default_factory=datetime.now)
    period_end: datetime = field(default_factory=datetime.now)


@dataclass
class ToolPerformanceBenchmark:
    """Performance benchmark for a tool"""

    tool_id: str
    benchmark_id: str

    # Benchmark details
    test_parameters: dict[str, Any]
    expected_result: Any

    # Performance results
    execution_times: list[float] = field(default_factory=list)
    memory_usage: list[float] = field(default_factory=list)
    success_rate: float = 1.0

    # Benchmark metadata
    environment: dict[str, str] = field(default_factory=dict)
    run_count: int = 0
    last_run: datetime = field(default_factory=datetime.now)


# ============================================================================
# Tool Plugin Types
# ============================================================================


@dataclass
class ToolPlugin:
    """Plugin definition for extending tool capabilities"""

    plugin_id: str
    name: str
    description: str

    # Plugin info
    version: str = "1.0.0"
    author: str = ""
    license: str = "Apache 2.0"

    # Plugin capabilities
    extends_tools: list[str] = field(default_factory=list)
    provides_tools: list[str] = field(default_factory=list)

    # Plugin configuration
    config_schema: dict[str, Any] = field(default_factory=dict)
    default_config: dict[str, Any] = field(default_factory=dict)

    # Dependencies
    required_packages: list[str] = field(default_factory=list)
    required_plugins: list[str] = field(default_factory=list)

    # Plugin metadata
    entry_point: str = ""
    installation_path: Path | None = None
    enabled: bool = True


@dataclass
class ToolExtension:
    """Extension to an existing tool"""

    extension_id: str
    base_tool_id: str
    extension_name: str

    # Extension capabilities
    additional_parameters: dict[str, Any] = field(default_factory=dict)
    parameter_modifiers: dict[str, Any] = field(default_factory=dict)

    # Processing hooks
    pre_execution_hooks: list[str] = field(default_factory=list)
    post_execution_hooks: list[str] = field(default_factory=list)

    # Extension metadata
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    enabled: bool = True


# ============================================================================
# Export all tool types
# ============================================================================

__all__ = [
    # Core tool types
    "ToolSpec",
    "ToolContext",
    "ToolCall",
    "ToolResult",
    # Registration and discovery
    "ToolRegistration",
    "ToolCategory",
    # Execution types
    "ToolExecutionRequest",
    "ToolExecutionStatus",
    "ToolExecutionLog",
    # Security types
    "ToolPermission",
    "ToolAuditLog",
    # Analytics types
    "ToolUsageStats",
    "ToolPerformanceBenchmark",
    # Plugin types
    "ToolPlugin",
    "ToolExtension",
]
