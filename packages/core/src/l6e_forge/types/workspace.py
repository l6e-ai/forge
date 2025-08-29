# l6e_forge/types/workspace.py
"""Workspace and template types for l6e-forge"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Literal, Union
from datetime import datetime
from pathlib import Path
import uuid

# ============================================================================
# Workspace Types
# ============================================================================


@dataclass
class WorkspaceMetadata:
    """Metadata about a workspace"""

    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    license: str = "Apache 2.0"

    # Workspace info
    created_at: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)
    forge_version: str = "0.1.0"

    # Workspace settings
    python_version: str = "3.9"
    tags: List[str] = field(default_factory=list)
    homepage: str = ""
    repository: str = ""


@dataclass
class WorkspaceStructure:
    """Structure of a workspace"""

    root_path: Path

    # Standard directories
    agents_dir: Path
    shared_dir: Path
    tools_dir: Path
    data_dir: Path
    logs_dir: Path

    # Configuration files
    config_file: Path
    env_file: Optional[Path] = None
    requirements_file: Optional[Path] = None

    # Optional directories
    tests_dir: Optional[Path] = None
    docs_dir: Optional[Path] = None
    scripts_dir: Optional[Path] = None

    def __post_init__(self):
        # Ensure all paths are absolute
        self.root_path = self.root_path.resolve()
        self.agents_dir = self.root_path / "agents"
        self.shared_dir = self.root_path / "shared"
        self.tools_dir = self.root_path / "tools"
        self.data_dir = self.root_path / "data"
        self.logs_dir = self.root_path / "logs"
        self.config_file = self.root_path / "forge.toml"


@dataclass
class WorkspaceState:
    """Current state of a workspace"""

    workspace_id: str
    status: Literal["active", "inactive", "error", "loading"] = "inactive"

    # Workspace contents
    agent_count: int = 0
    active_agents: List[str] = field(default_factory=list)
    failed_agents: List[str] = field(default_factory=list)

    # Runtime information
    runtime_pid: Optional[int] = None
    runtime_port: Optional[int] = None
    runtime_started_at: Optional[datetime] = None

    # Resource usage
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    disk_usage_mb: float = 0.0

    # Health information
    last_health_check: datetime = field(default_factory=datetime.now)
    health_score: float = 1.0
    health_issues: List[str] = field(default_factory=list)


# ============================================================================
# Template System Types
# ============================================================================


@dataclass
class TemplateVariable:
    """Template variable definition"""

    name: str
    description: str
    type: Literal["string", "integer", "float", "boolean", "array", "object"]
    default: Any = None
    required: bool = False

    # Validation
    choices: Optional[List[Any]] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    pattern: Optional[str] = None  # regex pattern for strings
    min_length: Optional[int] = None
    max_length: Optional[int] = None

    # UI hints
    ui_hint: Optional[
        Literal["text", "textarea", "select", "multiselect", "password"]
    ] = None
    placeholder: Optional[str] = None
    help_text: Optional[str] = None


@dataclass
class TemplateDependencies:
    """Template dependencies"""

    # Runtime dependencies
    python_packages: List[str] = field(default_factory=list)
    system_requirements: List[str] = field(default_factory=list)

    # Hardware requirements
    minimum_memory: str = "1GB"
    minimum_python_version: str = "3.9"
    requires_gpu: bool = False

    # Other templates this depends on
    template_dependencies: List[str] = field(default_factory=list)

    # External services
    external_services: List[str] = field(default_factory=list)


@dataclass
class TemplateFile:
    """File in a template"""

    path: str  # Relative path within template
    content: str  # Template content (Jinja2)

    # File metadata
    file_type: Literal["python", "toml", "yaml", "json", "markdown", "text"] = "text"
    executable: bool = False

    # Template processing
    is_template: bool = True  # False for static files
    encoding: str = "utf-8"

    # File conditions
    conditions: Dict[str, Any] = field(
        default_factory=dict
    )  # When to include this file


@dataclass
class TemplateSpec:
    """Complete template specification"""

    name: str
    description: str
    version: str = "1.0.0"
    category: str = "general"
    difficulty: Literal["beginner", "intermediate", "advanced"] = "beginner"

    # Template files
    files: List[TemplateFile] = field(default_factory=list)

    # Template variables
    variables: Dict[str, TemplateVariable] = field(default_factory=dict)

    # Dependencies
    dependencies: TemplateDependencies = field(
        default_factory=lambda: TemplateDependencies()
    )

    # Template metadata
    author: str = ""
    license: str = "Apache 2.0"
    tags: List[str] = field(default_factory=list)
    homepage: str = ""

    # Template settings
    post_generation_hooks: List[str] = field(default_factory=list)
    validation_rules: List[str] = field(default_factory=list)

    # Usage statistics
    usage_count: int = 0
    rating: float = 0.0
    last_used: Optional[datetime] = None


@dataclass
class TemplateContext:
    """Context for template generation"""

    template_spec: TemplateSpec
    variable_values: Dict[str, Any]

    # Generation context
    target_path: Path
    workspace_config: Dict[str, Any] = field(default_factory=dict)

    # Generation metadata
    generation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    generated_by: str = "system"
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class TemplateGenerationResult:
    """Result of template generation"""

    success: bool
    template_name: str
    target_path: Path

    # Generated files
    files_created: List[Path] = field(default_factory=list)
    files_modified: List[Path] = field(default_factory=list)

    # Generation info
    generation_time: float = 0.0
    variables_used: Dict[str, Any] = field(default_factory=dict)

    # Errors and warnings
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Post-generation actions
    hooks_executed: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)


# ============================================================================
# Project Management Types
# ============================================================================


@dataclass
class ProjectManifest:
    """Manifest file for an agent project"""

    project_name: str
    version: str = "1.0.0"
    description: str = ""

    # Project metadata
    author: str = ""
    license: str = "Apache 2.0"
    homepage: str = ""
    repository: str = ""

    # Project structure
    entry_point: str = "agent.py"
    agent_class: str = "Agent"

    # Dependencies
    dependencies: TemplateDependencies = field(
        default_factory=lambda: TemplateDependencies()
    )

    # Project configuration
    config_schema: Dict[str, Any] = field(default_factory=dict)
    default_config: Dict[str, Any] = field(default_factory=dict)

    # Project capabilities
    capabilities: List[str] = field(default_factory=list)
    tools_provided: List[str] = field(default_factory=list)

    # Build and deployment
    build_scripts: List[str] = field(default_factory=list)
    test_scripts: List[str] = field(default_factory=list)

    # Project metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class ProjectDependency:
    """Dependency of a project"""

    name: str
    version_constraint: str = "*"

    # Dependency type
    dependency_type: Literal["agent", "tool", "python", "system"] = "python"

    # Dependency metadata
    optional: bool = False
    development_only: bool = False

    # Resolution info
    resolved_version: Optional[str] = None
    installation_path: Optional[Path] = None

    # Dependency source
    source: Optional[str] = None  # registry, git, local, etc.
    source_url: Optional[str] = None


@dataclass
class ProjectEnvironment:
    """Environment configuration for a project"""

    environment_name: str

    # Environment settings
    python_version: str = "3.9"
    virtual_env_path: Optional[Path] = None

    # Environment variables
    env_vars: Dict[str, str] = field(default_factory=dict)
    env_file: Optional[Path] = None

    # Service dependencies
    required_services: List[str] = field(default_factory=list)
    service_configs: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Environment state
    is_active: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    last_activated: Optional[datetime] = None


# ============================================================================
# Workspace Operations Types
# ============================================================================


@dataclass
class WorkspaceOperation:
    """Record of a workspace operation"""

    operation_id: str
    operation_type: Literal[
        "create", "load", "save", "validate", "clean", "backup", "restore"
    ]

    # Operation details
    workspace_path: Path
    initiated_by: str = "system"

    # Operation status
    status: Literal["pending", "running", "completed", "failed", "cancelled"] = (
        "pending"
    )
    progress_percent: float = 0.0

    # Operation results
    success: bool = False
    result_data: Dict[str, Any] = field(default_factory=dict)

    # Error information
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)

    # Timing
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0


@dataclass
class WorkspaceBackup:
    """Workspace backup information"""

    backup_id: str
    workspace_name: str

    # Backup details
    backup_path: Path
    backup_size_bytes: int = 0

    # Backup contents
    includes_agents: bool = True
    includes_data: bool = True
    includes_config: bool = True
    includes_logs: bool = False

    # Backup metadata
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "system"

    # Backup validation
    checksum: str = ""
    verified: bool = False

    # Restoration info
    restorable: bool = True
    restore_notes: str = ""


@dataclass
class WorkspaceValidation:
    """Workspace validation results"""

    workspace_path: Path
    is_valid: bool = True

    # Validation checks
    structure_valid: bool = True
    config_valid: bool = True
    agents_valid: bool = True
    dependencies_satisfied: bool = True

    # Validation issues
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    # Validation metadata
    validated_at: datetime = field(default_factory=datetime.now)
    validation_version: str = "1.0.0"

    # Detailed results
    check_results: Dict[str, bool] = field(default_factory=dict)
    repair_suggestions: List[str] = field(default_factory=list)


# ============================================================================
# Workspace Discovery Types
# ============================================================================


@dataclass
class WorkspaceDiscoveryResult:
    """Result of workspace discovery"""

    # Discovery details
    search_paths: List[Path]
    workspaces_found: List[Path] = field(default_factory=list)

    # Discovery metadata
    discovery_time: float = 0.0
    discovered_at: datetime = field(default_factory=datetime.now)

    # Workspace details
    workspace_metadata: Dict[Path, WorkspaceMetadata] = field(default_factory=dict)
    workspace_health: Dict[Path, bool] = field(default_factory=dict)

    # Discovery issues
    invalid_workspaces: List[Path] = field(default_factory=list)
    access_denied: List[Path] = field(default_factory=list)
    discovery_errors: List[str] = field(default_factory=list)


@dataclass
class WorkspaceIndex:
    """Index of known workspaces"""

    # Index metadata
    index_version: str = "1.0.0"
    last_updated: datetime = field(default_factory=datetime.now)

    # Workspace entries
    workspaces: Dict[str, Path] = field(default_factory=dict)  # name -> path
    workspace_metadata: Dict[str, WorkspaceMetadata] = field(default_factory=dict)

    # Index statistics
    total_workspaces: int = 0
    active_workspaces: int = 0

    # Index settings
    auto_discovery: bool = True
    watch_paths: List[Path] = field(default_factory=list)

    # Cache information
    cache_valid: bool = True
    cache_expires_at: datetime = field(default_factory=datetime.now)


# ============================================================================
# Export all workspace types
# ============================================================================

__all__ = [
    # Workspace core types
    "WorkspaceMetadata",
    "WorkspaceStructure",
    "WorkspaceState",
    # Template types
    "TemplateVariable",
    "TemplateDependencies",
    "TemplateFile",
    "TemplateSpec",
    "TemplateContext",
    "TemplateGenerationResult",
    # Project types
    "ProjectManifest",
    "ProjectDependency",
    "ProjectEnvironment",
    # Operations types
    "WorkspaceOperation",
    "WorkspaceBackup",
    "WorkspaceValidation",
    # Discovery types
    "WorkspaceDiscoveryResult",
    "WorkspaceIndex",
]
