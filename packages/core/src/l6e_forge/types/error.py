# l6e_forge/types/error.py
"""Error and status types for l6e-forge"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Literal
from datetime import datetime
from enum import Enum
import uuid

# ============================================================================
# Error Classification Types
# ============================================================================


class ErrorType(Enum):
    """Types of errors in the system"""

    VALIDATION_ERROR = "validation_error"
    CONFIGURATION_ERROR = "configuration_error"
    MODEL_ERROR = "model_error"
    TOOL_ERROR = "tool_error"
    MEMORY_ERROR = "memory_error"
    TIMEOUT_ERROR = "timeout_error"
    PERMISSION_ERROR = "permission_error"
    RESOURCE_ERROR = "resource_error"
    AGENT_ERROR = "agent_error"
    SYSTEM_ERROR = "system_error"
    NETWORK_ERROR = "network_error"
    AUTHENTICATION_ERROR = "authentication_error"
    NOT_FOUND_ERROR = "not_found_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    DEPENDENCY_ERROR = "dependency_error"


class ErrorSeverity(Enum):
    """Severity levels for errors"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================================
# Core Error Types
# ============================================================================


@dataclass
class AgentError:
    """Error information"""

    error_type: ErrorType
    message: str
    severity: ErrorSeverity = ErrorSeverity.MEDIUM

    # Context
    agent_id: Optional[str] = None
    tool_id: Optional[str] = None
    conversation_id: Optional[str] = None
    model_id: Optional[str] = None

    # Technical details
    exception_type: Optional[str] = None
    stack_trace: Optional[str] = None
    error_code: Optional[str] = None

    # Timing
    timestamp: datetime = field(default_factory=datetime.now)

    # Recovery info
    recoverable: bool = True
    suggested_action: Optional[str] = None
    retry_after_seconds: Optional[int] = None

    # Error metadata
    error_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: Optional[str] = None

    # Additional context
    context_data: Dict[str, Any] = field(default_factory=dict)
    user_message: Optional[str] = None  # User-friendly error message


@dataclass
class ErrorContext:
    """Context information for error reporting"""

    # System context
    component: str
    operation: str

    # Request context
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None

    # Environment context
    environment: str = "development"
    version: str = "unknown"

    # Additional context
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Timing
    timestamp: datetime = field(default_factory=datetime.now)


# ============================================================================
# Health and Status Types
# ============================================================================


@dataclass
class HealthStatus:
    """Health check status"""

    healthy: bool
    status: Literal["healthy", "degraded", "unhealthy", "unknown"]

    # Details
    checks: Dict[str, bool] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)

    # Timing
    last_check: datetime = field(default_factory=datetime.now)
    check_duration: float = 0.0

    # Issues
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Health metadata
    component: str = "unknown"
    version: str = "unknown"


@dataclass
class ServiceStatus:
    """Status of a system service"""

    service_name: str
    status: Literal["running", "stopped", "starting", "stopping", "error", "unknown"]

    # Service health
    health: HealthStatus

    # Service metadata
    version: str = "unknown"
    uptime_seconds: float = 0.0
    restart_count: int = 0

    # Service metrics
    cpu_usage_percent: float = 0.0
    memory_usage_mb: float = 0.0

    # Last status change
    status_changed_at: datetime = field(default_factory=datetime.now)
    last_heartbeat: datetime = field(default_factory=datetime.now)


@dataclass
class SystemHealth:
    """Overall system health"""

    overall_status: Literal["healthy", "degraded", "unhealthy", "unknown"]

    # Component health
    component_health: Dict[str, HealthStatus] = field(default_factory=dict)
    service_health: Dict[str, ServiceStatus] = field(default_factory=dict)

    # System metrics
    system_metrics: Dict[str, float] = field(default_factory=dict)

    # Health summary
    healthy_components: int = 0
    total_components: int = 0
    critical_issues: List[str] = field(default_factory=list)

    # Timing
    last_updated: datetime = field(default_factory=datetime.now)
    check_interval_seconds: int = 30


# ============================================================================
# Error Handling Types
# ============================================================================


@dataclass
class ErrorHandler:
    """Error handler configuration"""

    handler_id: str
    name: str

    # Handler conditions
    error_types: List[ErrorType] = field(default_factory=list)
    severity_levels: List[ErrorSeverity] = field(default_factory=list)
    component_patterns: List[str] = field(default_factory=list)

    # Handler actions
    action_type: Literal["log", "notify", "retry", "escalate", "ignore"] = "log"
    action_config: Dict[str, Any] = field(default_factory=dict)

    # Handler settings
    enabled: bool = True
    priority: int = 5

    # Handler metadata
    created_at: datetime = field(default_factory=datetime.now)
    execution_count: int = 0


@dataclass
class ErrorRecoveryStrategy:
    """Strategy for recovering from errors"""

    strategy_id: str
    name: str
    description: str

    # Recovery conditions
    applicable_errors: List[ErrorType] = field(default_factory=list)
    max_severity: ErrorSeverity = ErrorSeverity.HIGH

    # Recovery steps
    recovery_steps: List[str] = field(default_factory=list)
    automated: bool = True

    # Recovery settings
    max_attempts: int = 3
    retry_delay_seconds: int = 60
    exponential_backoff: bool = True

    # Success criteria
    success_checks: List[str] = field(default_factory=list)
    timeout_seconds: int = 300

    # Strategy metadata
    success_rate: float = 0.0
    last_used: Optional[datetime] = None


# ============================================================================
# Error Reporting Types
# ============================================================================


@dataclass
class ErrorReport:
    """Detailed error report"""

    report_id: str
    error: AgentError
    context: ErrorContext

    # Report details
    impact_assessment: str = ""
    reproduction_steps: List[str] = field(default_factory=list)

    # Related information
    related_errors: List[str] = field(default_factory=list)
    similar_incidents: List[str] = field(default_factory=list)

    # Resolution information
    resolution_status: Literal["open", "investigating", "resolved", "wont_fix"] = "open"
    resolution_notes: str = ""
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None

    # Report metadata
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "system"
    priority: int = 5


@dataclass
class ErrorSummary:
    """Summary of errors over a time period"""

    # Time period
    period_start: datetime
    period_end: datetime

    # Error counts
    total_errors: int = 0
    errors_by_type: Dict[ErrorType, int] = field(default_factory=dict)
    errors_by_severity: Dict[ErrorSeverity, int] = field(default_factory=dict)
    errors_by_component: Dict[str, int] = field(default_factory=dict)

    # Top errors
    most_common_errors: List[str] = field(default_factory=list)
    most_critical_errors: List[str] = field(default_factory=list)

    # Trends
    error_rate_trend: Literal["increasing", "decreasing", "stable"] = "stable"
    new_error_types: List[ErrorType] = field(default_factory=list)

    # Resolution stats
    resolved_errors: int = 0
    avg_resolution_time: float = 0.0

    # Summary metadata
    generated_at: datetime = field(default_factory=datetime.now)


# ============================================================================
# Monitoring and Alerting Types
# ============================================================================


@dataclass
class AlertRule:
    """Rule for triggering alerts"""

    rule_id: str
    name: str
    description: str

    # Trigger conditions
    error_types: List[ErrorType] = field(default_factory=list)
    severity_threshold: ErrorSeverity = ErrorSeverity.HIGH
    error_count_threshold: int = 5
    time_window_minutes: int = 60

    # Alert settings
    alert_channels: List[str] = field(default_factory=list)
    cooldown_minutes: int = 30

    # Rule metadata
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)

    # Rule statistics
    trigger_count: int = 0
    last_triggered: Optional[datetime] = None


@dataclass
class Alert:
    """System alert"""

    alert_id: str
    rule_id: str

    # Alert details
    title: str
    message: str
    severity: ErrorSeverity

    # Alert context
    triggered_by_errors: List[str] = field(default_factory=list)
    affected_components: List[str] = field(default_factory=list)

    # Alert state
    status: Literal["active", "acknowledged", "resolved"] = "active"
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None

    # Alert timing
    triggered_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None

    # Alert metadata
    escalation_level: int = 1
    notification_count: int = 0


# ============================================================================
# Performance and Reliability Types
# ============================================================================


@dataclass
class ReliabilityMetrics:
    """System reliability metrics"""

    # Uptime metrics
    uptime_percentage: float = 99.0
    total_uptime_seconds: float = 0.0
    total_downtime_seconds: float = 0.0

    # Error metrics
    error_rate: float = 0.0
    mean_time_between_failures: float = 0.0
    mean_time_to_recovery: float = 0.0

    # Performance metrics
    avg_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0

    # Availability metrics
    availability_percentage: float = 99.0
    planned_downtime_seconds: float = 0.0
    unplanned_downtime_seconds: float = 0.0

    # Metrics period
    period_start: datetime = field(default_factory=datetime.now)
    period_end: datetime = field(default_factory=datetime.now)


@dataclass
class PerformanceBaseline:
    """Baseline performance metrics"""

    component: str

    # Response time baselines
    baseline_response_time: float = 1.0
    response_time_variance: float = 0.1

    # Throughput baselines
    baseline_throughput: float = 100.0  # requests per second
    throughput_variance: float = 0.1

    # Resource usage baselines
    baseline_cpu_usage: float = 50.0
    baseline_memory_usage: float = 512.0  # MB

    # Error rate baselines
    baseline_error_rate: float = 0.01  # 1%

    # Baseline metadata
    established_at: datetime = field(default_factory=datetime.now)
    confidence_level: float = 0.95
    sample_size: int = 1000


# ============================================================================
# Export all error types
# ============================================================================

__all__ = [
    # Error classification
    "ErrorType",
    "ErrorSeverity",
    # Core error types
    "AgentError",
    "ErrorContext",
    # Health and status
    "HealthStatus",
    "ServiceStatus",
    "SystemHealth",
    # Error handling
    "ErrorHandler",
    "ErrorRecoveryStrategy",
    # Error reporting
    "ErrorReport",
    "ErrorSummary",
    # Monitoring and alerting
    "AlertRule",
    "Alert",
    # Performance and reliability
    "ReliabilityMetrics",
    "PerformanceBaseline",
]
