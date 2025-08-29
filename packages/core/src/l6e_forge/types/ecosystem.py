# l6e_forge/types/ecosystem.py
"""Package distribution and ecosystem types for l6e-forge"""

from dataclasses import dataclass, field
from typing import Any, Literal
from datetime import datetime
from pathlib import Path
import uuid

# ============================================================================
# Package Types
# ============================================================================


@dataclass
class AgentPackageMetadata:
    """Package metadata"""

    name: str
    version: str
    description: str
    author: str
    license: str
    homepage: str

    # Package info
    package_format_version: str = "1.0"
    created_at: datetime = field(default_factory=datetime.now)
    file_size: int = 0
    checksum: str = ""

    # Compatibility
    min_forge_version: str = "0.1.0"
    max_forge_version: str | None = None
    python_version: str = ">=3.9"
    platform: list[str] = field(default_factory=lambda: ["any"])

    # Categories and tags
    category: str = "general"
    tags: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)

    # Quality metrics
    downloads: int = 0
    rating: float = 0.0
    rating_count: int = 0

    # Package status
    status: Literal["active", "deprecated", "yanked"] = "active"
    deprecation_message: str | None = None


@dataclass
class PackageDependencies:
    """Package dependencies specification"""

    # Runtime dependencies
    python_packages: dict[str, str] = field(
        default_factory=dict
    )  # name -> version_spec
    system_packages: list[str] = field(default_factory=list)

    # Agent dependencies (other agents this one depends on)
    agent_dependencies: dict[str, str] = field(
        default_factory=dict
    )  # name -> version_spec

    # Tool dependencies
    tool_dependencies: dict[str, str] = field(default_factory=dict)

    # Model requirements
    required_models: list[str] = field(default_factory=list)
    recommended_models: list[str] = field(default_factory=list)

    # Hardware requirements
    min_memory_gb: float = 1.0
    min_gpu_memory_gb: float = 0.0
    requires_gpu: bool = False
    requires_internet: bool = False

    # Optional dependencies
    optional_dependencies: dict[str, dict[str, str]] = field(
        default_factory=dict
    )  # group -> {name: version}


@dataclass
class AgentPackage:
    """Distributable agent package"""

    metadata: AgentPackageMetadata
    dependencies: PackageDependencies

    # Package contents
    files: dict[str, bytes] = field(default_factory=dict)  # filename -> file_content

    # Package verification
    signature: str | None = None  # For signed packages
    signature_algorithm: str | None = None

    # Package build info
    build_info: dict[str, Any] = field(default_factory=dict)
    built_at: datetime = field(default_factory=datetime.now)
    built_by: str = ""

    # Installation info
    installation_scripts: dict[str, str] = field(
        default_factory=dict
    )  # script_name -> content
    post_install_hooks: list[str] = field(default_factory=list)


@dataclass
class PackageVersion:
    """Specific version of a package"""

    package_name: str
    version: str

    # Version metadata
    is_prerelease: bool = False
    is_yanked: bool = False
    yanked_reason: str | None = None

    # Release information
    release_date: datetime = field(default_factory=datetime.now)
    release_notes: str = ""
    changelog: str = ""

    # Download information
    download_url: str = ""
    download_count: int = 0
    file_hash: str = ""

    # Version dependencies
    dependencies: PackageDependencies = field(
        default_factory=lambda: PackageDependencies()
    )

    # Compatibility
    breaking_changes: list[str] = field(default_factory=list)
    migration_guide: str = ""


# ============================================================================
# Registry Types
# ============================================================================


@dataclass
class PackageRegistry:
    """Agent package registry configuration"""

    name: str
    url: str
    type: Literal["http", "git", "local", "s3"] = "http"

    # Authentication
    auth_required: bool = False
    auth_method: Literal["token", "basic", "oauth", "ssh_key"] | None = None
    auth_config: dict[str, str] = field(default_factory=dict)

    # Trust settings
    verify_signatures: bool = True
    trusted_publishers: list[str] = field(default_factory=list)
    trust_level: Literal["high", "medium", "low"] = "medium"

    # Caching
    cache_packages: bool = True
    cache_duration_hours: int = 24
    cache_location: Path | None = None

    # Registry metadata
    description: str = ""
    maintainer: str = ""
    registry_version: str = "1.0.0"

    # Registry statistics
    package_count: int = 0
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class RegistryConfig:
    """Registry system configuration"""

    # Default registries
    registries: list[PackageRegistry] = field(default_factory=list)

    # Installation settings
    default_registry: str = "official"
    allow_prerelease: bool = False
    auto_update_check: bool = True
    verify_checksums: bool = True

    # Security settings
    allow_unsigned_packages: bool = False
    quarantine_suspicious_packages: bool = True
    scan_for_malware: bool = True

    # Performance settings
    parallel_downloads: int = 3
    download_timeout: int = 300
    retry_attempts: int = 3


@dataclass
class PackageSearchResult:
    """Result from package search"""

    package_name: str
    latest_version: str
    description: str

    # Search relevance
    relevance_score: float = 0.0
    match_type: Literal["exact", "prefix", "fuzzy", "description"] = "fuzzy"

    # Package metadata
    author: str = ""
    category: str = ""
    tags: list[str] = field(default_factory=list)
    downloads: int = 0
    rating: float = 0.0

    # Registry information
    registry_name: str = ""
    registry_url: str = ""

    # Additional versions
    available_versions: list[str] = field(default_factory=list)


# ============================================================================
# Package Installation Types
# ============================================================================


@dataclass
class InstallationRequest:
    """Request to install a package"""

    package_name: str
    version_constraint: str = "*"

    # Installation options
    registry: str | None = None
    force_reinstall: bool = False
    no_dependencies: bool = False

    # Installation target
    target_workspace: Path | None = None
    install_location: Path | None = None

    # Installation metadata
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    requested_by: str = "user"
    requested_at: datetime = field(default_factory=datetime.now)


@dataclass
class InstallationPlan:
    """Plan for package installation"""

    primary_package: str

    # Installation steps
    packages_to_install: list[tuple[str, str]] = field(
        default_factory=list
    )  # (name, version)
    packages_to_upgrade: list[tuple[str, str, str]] = field(
        default_factory=list
    )  # (name, from_version, to_version)
    packages_to_remove: list[str] = field(default_factory=list)

    # Dependency resolution
    dependency_tree: dict[str, list[str]] = field(default_factory=dict)
    conflicts: list[str] = field(default_factory=list)

    # Installation metadata
    total_download_size: int = 0
    estimated_install_time: int = 0
    requires_restart: bool = False

    # Plan validation
    plan_valid: bool = True
    validation_errors: list[str] = field(default_factory=list)


@dataclass
class InstallationResult:
    """Result of package installation"""

    request: InstallationRequest
    success: bool

    # Installation details
    installed_packages: list[str] = field(default_factory=list)
    failed_packages: list[str] = field(default_factory=list)

    # Installation info
    installation_time: float = 0.0
    bytes_downloaded: int = 0

    # Installation artifacts
    installation_log: str = ""
    installed_files: list[Path] = field(default_factory=list)

    # Error information
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    # Post-installation
    requires_configuration: bool = False
    configuration_instructions: str = ""


@dataclass
class InstalledPackage:
    """Record of an installed package"""

    package_name: str
    version: str

    # Package location
    installation_path: Path

    # Package files
    package_files: list[Path] = field(default_factory=list)

    # Installation metadata
    installed_at: datetime = field(default_factory=datetime.now)
    installed_by: str = "user"
    installation_method: Literal["registry", "local", "git", "url"] = "registry"

    # Package state
    is_active: bool = True
    is_editable: bool = False

    # Dependency information
    depends_on: list[str] = field(default_factory=list)
    required_by: list[str] = field(default_factory=list)

    # Installation verification
    checksum_verified: bool = False
    signature_verified: bool = False

    # Package metadata cache
    cached_metadata: AgentPackageMetadata | None = None


# ============================================================================
# Publishing Types
# ============================================================================


@dataclass
class PublishingCredentials:
    """Credentials for publishing packages"""

    registry_name: str

    # Authentication
    username: str | None = None
    password: str | None = None
    api_token: str | None = None

    # Publishing permissions
    can_publish: bool = True
    can_yank: bool = False
    can_manage: bool = False

    # Credential metadata
    expires_at: datetime | None = None
    last_used: datetime | None = None


@dataclass
class PublishingRequest:
    """Request to publish a package"""

    package: AgentPackage
    registry: str

    # Publishing options
    replace_existing: bool = False
    dry_run: bool = False

    # Publishing metadata
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    submitted_by: str = ""
    submitted_at: datetime = field(default_factory=datetime.now)


@dataclass
class PublishingResult:
    """Result of package publishing"""

    request: PublishingRequest
    success: bool

    # Publishing details
    package_url: str = ""
    version_published: str = ""

    # Publishing info
    upload_time: float = 0.0
    bytes_uploaded: int = 0

    # Validation results
    validation_passed: bool = True
    validation_warnings: list[str] = field(default_factory=list)
    validation_errors: list[str] = field(default_factory=list)

    # Publishing metadata
    published_at: datetime | None = None
    registry_response: dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Marketplace Types
# ============================================================================


@dataclass
class PackageReview:
    """User review of a package"""

    review_id: str
    package_name: str
    package_version: str

    # Review content
    rating: int  # 1-5 stars
    title: str = ""
    review_text: str = ""

    # Review metadata
    reviewer_id: str = ""
    reviewer_name: str = "Anonymous"
    reviewed_at: datetime = field(default_factory=datetime.now)

    # Review verification
    verified_download: bool = False
    verified_usage: bool = False

    # Review interaction
    helpful_votes: int = 0
    total_votes: int = 0


@dataclass
class PackageStats:
    """Statistics for a package"""

    package_name: str

    # Download statistics
    total_downloads: int = 0
    monthly_downloads: int = 0
    weekly_downloads: int = 0
    daily_downloads: int = 0

    # Rating statistics
    average_rating: float = 0.0
    rating_distribution: dict[int, int] = field(default_factory=dict)  # rating -> count
    review_count: int = 0

    # Usage statistics
    active_installations: int = 0
    retention_rate: float = 0.0

    # Trend data
    download_trend: Literal["growing", "stable", "declining"] = "stable"
    popularity_rank: int = 0

    # Statistics metadata
    last_updated: datetime = field(default_factory=datetime.now)
    stats_period_days: int = 30


@dataclass
class PackageCollection:
    """Curated collection of packages"""

    collection_id: str
    name: str
    description: str

    # Collection contents
    packages: list[str] = field(default_factory=list)
    featured_packages: list[str] = field(default_factory=list)

    # Collection metadata
    curator: str = ""
    category: str = "general"
    tags: list[str] = field(default_factory=list)

    # Collection stats
    follower_count: int = 0
    package_count: int = 0

    # Collection state
    is_public: bool = True
    is_featured: bool = False

    # Collection timing
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


# ============================================================================
# Security Types
# ============================================================================


@dataclass
class SecurityScan:
    """Security scan of a package"""

    scan_id: str
    package_name: str
    package_version: str

    # Scan results
    security_score: float = 0.0  # 0-10, higher is better
    vulnerabilities_found: int = 0

    # Vulnerability details
    critical_issues: list[str] = field(default_factory=list)
    high_issues: list[str] = field(default_factory=list)
    medium_issues: list[str] = field(default_factory=list)
    low_issues: list[str] = field(default_factory=list)

    # Scan metadata
    scanned_at: datetime = field(default_factory=datetime.now)
    scanner_version: str = "1.0.0"
    scan_duration: float = 0.0

    # Scan configuration
    scan_type: Literal["static", "dynamic", "comprehensive"] = "static"
    scan_tools: list[str] = field(default_factory=list)


@dataclass
class SecurityPolicy:
    """Security policy for packages"""

    policy_id: str
    name: str
    description: str

    # Policy rules
    min_security_score: float = 7.0
    max_vulnerabilities: dict[str, int] = field(
        default_factory=dict
    )  # severity -> max_count

    # Package restrictions
    blocked_packages: list[str] = field(default_factory=list)
    allowed_publishers: list[str] = field(default_factory=list)

    # Scanning requirements
    require_security_scan: bool = True
    max_scan_age_days: int = 30

    # Policy metadata
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)

    # Policy application
    applies_to: list[str] = field(default_factory=list)  # registry names
    enforcement_level: Literal["strict", "advisory", "disabled"] = "advisory"


# ============================================================================
# Export all ecosystem types
# ============================================================================

__all__ = [
    # Package types
    "AgentPackageMetadata",
    "PackageDependencies",
    "AgentPackage",
    "PackageVersion",
    # Registry types
    "PackageRegistry",
    "RegistryConfig",
    "PackageSearchResult",
    # Installation types
    "InstallationRequest",
    "InstallationPlan",
    "InstallationResult",
    "InstalledPackage",
    # Publishing types
    "PublishingCredentials",
    "PublishingRequest",
    "PublishingResult",
    # Marketplace types
    "PackageReview",
    "PackageStats",
    "PackageCollection",
    # Security types
    "SecurityScan",
    "SecurityPolicy",
]
