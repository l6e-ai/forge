# l6e_forge/types/__init__.py
"""
l6e-forge Type System

This module provides comprehensive type definitions for all components
of the l6e-forge system, organized into logical modules.
"""

# ============================================================================
# Core Types - Essential data structures
# ============================================================================


# ============================================================================
# Configuration Types - All configuration structures
# ============================================================================

from .config import (
    # Workspace configuration
    WorkspaceInfo,
    WorkspaceConfig,
    RuntimeConfig,
    ModelsConfig,
    MonitoringConfig,
    # Agent configuration
    AgentInfo,
    AgentConfig,
    ModelConfig,
    PersonalityConfig,
    CapabilitiesConfig,
    BehaviorConfig,
    DevelopmentConfig,
    # System configuration
    MemoryConfig,
    ToolsConfig,
    # Security and environment
    SandboxConfig,
    PermissionConfig,
    EnvironmentConfig,
    # Advanced configuration
    MetricsConfig,
    TracingConfig,
)

# ============================================================================
# Agent Types - Agent-specific data structures
# ============================================================================

from .agent import (
    # Core agent types
    AgentStatus,
    AgentSpec,
    AgentInstance,
    # Capability types
    Capability,
    AgentProfile,
    # Communication types
    AgentConversation,
    AgentTeam,
    # Learning types
    LearningEvent,
    AgentKnowledgeBase,
)

# ============================================================================
# Model Types - LLM and model management
# ============================================================================

from .model import (
    # Model specification
    ModelSpec,
    ModelInstance,
    # Request/Response types
    CompletionRequest,
    CompletionResponse,
    ChatRequest,
    ChatResponse,
    StreamingChunk,
    # Provider types
    ProviderConfig,
    ProviderStatus,
    # Performance types
    ModelPerformanceMetrics,
    ModelUsagePattern,
    # Management types
    ModelLoadRequest,
    ModelUnloadRequest,
    ModelOptimizationConfig,
)

# ============================================================================
# Memory Types - Memory system structures
# ============================================================================

from .memory import (
    # Core memory types
    MemoryEntry,
    MemoryResult,
    MemoryQuery,
    # Collection types
    MemoryCollection,
    MemoryNamespace,
    # Conversation memory
    ConversationMemory,
    SessionMemory,
    # Analytics types
    MemoryUsageStats,
    MemoryHealth,
    # Operations types
    MemoryOperation,
    MemoryBatch,
    # Configuration types
    VectorStoreConfig,
    KVStoreConfig,
    MemoryIndexConfig,
)

# ============================================================================
# Tool Types - Tool system structures
# ============================================================================

from .tool import (
    # Core tool types
    ToolSpec,
    ToolContext,
    ToolCall,
    ToolResult,
    # Registration and discovery
    ToolRegistration,
    ToolCategory,
    # Execution types
    ToolExecutionRequest,
    ToolExecutionStatus,
    ToolExecutionLog,
    # Security types
    ToolPermission,
    ToolAuditLog,
    # Analytics types
    ToolUsageStats,
    ToolPerformanceBenchmark,
    # Plugin types
    ToolPlugin,
    ToolExtension,
)

# ============================================================================
# Event Types - Event system structures
# ============================================================================

from .event import (
    # Core event types
    Event,
    EventHandler,
    AsyncEventHandler,
    EventSubscription,
    # Event bus types
    EventBusConfig,
    EventRoute,
    # Standard event types
    AgentEvent,
    ConversationEvent,
    SystemEvent,
    # Processing types
    EventProcessingResult,
    EventBatch,
    EventQueue,
    # Analytics types
    EventStats,
    EventTrace,
    # Pattern types
    EventPattern,
    EventCorrelation,
    # Middleware types
    EventMiddleware,
    EventFilter,
)

# ============================================================================
# Error Types - Error handling and status
# ============================================================================

from .error import (
    # Error classification
    ErrorType,
    ErrorSeverity,
    # Core error types
    AgentError,
    ErrorContext,
    # Health and status
    HealthStatus,
    ServiceStatus,
    SystemHealth,
    # Error handling
    ErrorHandler,
    ErrorRecoveryStrategy,
    # Error reporting
    ErrorReport,
    ErrorSummary,
    # Monitoring and alerting
    AlertRule,
    Alert,
    # Performance and reliability
    ReliabilityMetrics,
    PerformanceBaseline,
)

# ============================================================================
# Workspace Types - Project and template management
# ============================================================================

from .workspace import (
    # Workspace core types
    WorkspaceMetadata,
    WorkspaceStructure,
    WorkspaceState,
    # Template types
    TemplateVariable,
    TemplateDependencies,
    TemplateFile,
    TemplateSpec,
    TemplateContext,
    TemplateGenerationResult,
    # Project types
    ProjectManifest,
    ProjectDependency,
    ProjectEnvironment,
    # Operations types
    WorkspaceOperation,
    WorkspaceBackup,
    WorkspaceValidation,
    # Discovery types
    WorkspaceDiscoveryResult,
    WorkspaceIndex,
)

# ============================================================================
# Testing Types - Testing framework structures
# ============================================================================

from .testing import (
    # Test definition types
    TestCase,
    TestSuite,
    TestScenario,
    # Test execution types
    TestEnvironment,
    TestExecution,
    TestResult,
    TestRun,
    # Configuration types
    TestConfig,
    MockConfig,
    # Assertion types
    Assertion,
    AssertionGroup,
    # Test data types
    TestData,
    TestDataSet,
    # Reporting types
    TestReport,
    TestMetrics,
    # Performance testing types
    PerformanceTest,
    PerformanceResult,
)

# ============================================================================
# Ecosystem Types - Package distribution and marketplace
# ============================================================================

from .ecosystem import (
    # Package types
    AgentPackageMetadata,
    PackageDependencies,
    AgentPackage,
    PackageVersion,
    # Registry types
    PackageRegistry,
    RegistryConfig,
    PackageSearchResult,
    # Installation types
    InstallationRequest,
    InstallationPlan,
    InstallationResult,
    InstalledPackage,
    # Publishing types
    PublishingCredentials,
    PublishingRequest,
    PublishingResult,
    # Marketplace types
    PackageReview,
    PackageStats,
    PackageCollection,
    # Security types
    SecurityScan,
    SecurityPolicy,
)

# ============================================================================
# Type Categories for Convenience
# ============================================================================

# Core system types
CORE_TYPES = [
    "AgentID",
    "ConversationID",
    "SessionID",
    "ModelID",
    "ToolID",
    "EventID",
    "SubscriptionID",
    "TaskID",
    "Message",
    "Attachment",
    "AgentContext",
    "AgentResponse",
]

# Configuration types
CONFIG_TYPES = [
    "WorkspaceConfig",
    "AgentConfig",
    "ModelConfig",
    "MemoryConfig",
    "ToolsConfig",
    "RuntimeConfig",
    "MonitoringConfig",
]

# Runtime types
RUNTIME_TYPES = [
    "AgentSpec",
    "AgentInstance",
    "ModelInstance",
    "ToolCall",
    "Event",
    "MemoryEntry",
    "MemoryResult",
]

# Interface types
INTERFACE_TYPES = [
    "IAgent",
    "IRuntime",
    "IMemoryManager",
    "IModelManager",
    "IToolRegistry",
    "IEventBus",
]

# Error and status types
STATUS_TYPES = [
    "ErrorType",
    "ErrorSeverity",
    "AgentError",
    "HealthStatus",
    "ServiceStatus",
    "SystemHealth",
]

# ============================================================================
# Utility Functions
# ============================================================================


def get_type_categories() -> dict[str, list[str]]:
    """Get all type categories"""
    return {
        "core": CORE_TYPES,
        "config": CONFIG_TYPES,
        "runtime": RUNTIME_TYPES,
        "interfaces": INTERFACE_TYPES,
        "status": STATUS_TYPES,
    }


def get_all_types() -> list[str]:
    """Get list of all exported types"""
    return [
        name for name in globals() if not name.startswith("_") and name[0].isupper()
    ]


def is_config_type(type_name: str) -> bool:
    """Check if a type is a configuration type"""
    return type_name in CONFIG_TYPES or type_name.endswith("Config")


def is_error_type(type_name: str) -> bool:
    """Check if a type is an error or status type"""
    return type_name in STATUS_TYPES or "Error" in type_name or "Status" in type_name


# ============================================================================
# Version Information
# ============================================================================

__version__ = "0.1.0"
__author__ = "l6e-forge Team"
__license__ = "Apache 2.0"

# Type system metadata
TYPE_SYSTEM_VERSION = "1.0.0"
SUPPORTED_PYTHON_VERSIONS = ["3.9", "3.10", "3.11", "3.12"]

# ============================================================================
# All Exports
# ============================================================================

__all__ = [
    # Core types
    *CORE_TYPES,
    # Configuration types
    "WorkspaceInfo",
    "WorkspaceConfig",
    "RuntimeConfig",
    "ModelsConfig",
    "MonitoringConfig",
    "AgentInfo",
    "AgentConfig",
    "ModelConfig",
    "PersonalityConfig",
    "CapabilitiesConfig",
    "BehaviorConfig",
    "DevelopmentConfig",
    "MemoryConfig",
    "ToolsConfig",
    "SandboxConfig",
    "PermissionConfig",
    "EnvironmentConfig",
    "MetricsConfig",
    "TracingConfig",
    # Agent types
    "AgentStatus",
    "AgentSpec",
    "AgentInstance",
    "Capability",
    "AgentProfile",
    "AgentConversation",
    "AgentTeam",
    "LearningEvent",
    "AgentKnowledgeBase",
    # Model types
    "ModelSpec",
    "ModelInstance",
    "CompletionRequest",
    "CompletionResponse",
    "ChatRequest",
    "ChatResponse",
    "StreamingChunk",
    "ProviderConfig",
    "ProviderStatus",
    "ModelPerformanceMetrics",
    "ModelUsagePattern",
    "ModelLoadRequest",
    "ModelUnloadRequest",
    "ModelOptimizationConfig",
    # Memory types
    "MemoryEntry",
    "MemoryResult",
    "MemoryQuery",
    "MemoryCollection",
    "MemoryNamespace",
    "ConversationMemory",
    "SessionMemory",
    "MemoryUsageStats",
    "MemoryHealth",
    "MemoryOperation",
    "MemoryBatch",
    "VectorStoreConfig",
    "KVStoreConfig",
    "MemoryIndexConfig",
    # Tool types
    "ToolSpec",
    "ToolContext",
    "ToolCall",
    "ToolResult",
    "ToolRegistration",
    "ToolCategory",
    "ToolExecutionRequest",
    "ToolExecutionStatus",
    "ToolExecutionLog",
    "ToolPermission",
    "ToolAuditLog",
    "ToolUsageStats",
    "ToolPerformanceBenchmark",
    "ToolPlugin",
    "ToolExtension",
    # Event types
    "Event",
    "EventHandler",
    "AsyncEventHandler",
    "EventSubscription",
    "EventBusConfig",
    "EventRoute",
    "AgentEvent",
    "ConversationEvent",
    "SystemEvent",
    "EventProcessingResult",
    "EventBatch",
    "EventQueue",
    "EventStats",
    "EventTrace",
    "EventPattern",
    "EventCorrelation",
    "EventMiddleware",
    "EventFilter",
    # Error types
    "ErrorType",
    "ErrorSeverity",
    "AgentError",
    "ErrorContext",
    "HealthStatus",
    "ServiceStatus",
    "SystemHealth",
    "ErrorHandler",
    "ErrorRecoveryStrategy",
    "ErrorReport",
    "ErrorSummary",
    "AlertRule",
    "Alert",
    "ReliabilityMetrics",
    "PerformanceBaseline",
    # Workspace types
    "WorkspaceMetadata",
    "WorkspaceStructure",
    "WorkspaceState",
    "TemplateVariable",
    "TemplateDependencies",
    "TemplateFile",
    "TemplateSpec",
    "TemplateContext",
    "TemplateGenerationResult",
    "ProjectManifest",
    "ProjectDependency",
    "ProjectEnvironment",
    "WorkspaceOperation",
    "WorkspaceBackup",
    "WorkspaceValidation",
    "WorkspaceDiscoveryResult",
    "WorkspaceIndex",
    # Testing types
    "TestCase",
    "TestSuite",
    "TestScenario",
    "TestEnvironment",
    "TestExecution",
    "TestResult",
    "TestRun",
    "TestConfig",
    "MockConfig",
    "Assertion",
    "AssertionGroup",
    "TestData",
    "TestDataSet",
    "TestReport",
    "TestMetrics",
    "PerformanceTest",
    "PerformanceResult",
    # Ecosystem types
    "AgentPackageMetadata",
    "PackageDependencies",
    "AgentPackage",
    "PackageVersion",
    "PackageRegistry",
    "RegistryConfig",
    "PackageSearchResult",
    "InstallationRequest",
    "InstallationPlan",
    "InstallationResult",
    "InstalledPackage",
    "PublishingCredentials",
    "PublishingRequest",
    "PublishingResult",
    "PackageReview",
    "PackageStats",
    "PackageCollection",
    "SecurityScan",
    "SecurityPolicy",
    # Utility functions
    "get_type_categories",
    "get_all_types",
    "is_protocol_type",
    "is_config_type",
    "is_error_type",
    # Version info
    "__version__",
    "TYPE_SYSTEM_VERSION",
]
