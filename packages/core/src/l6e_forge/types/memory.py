# l6e_forge/types/memory.py
"""Memory system types for l6e-forge"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Literal
from datetime import datetime
import uuid
from l6e_forge.types.core import ConversationID, AgentID

# ============================================================================
# Memory Storage Types
# ============================================================================


@dataclass
class MemoryEntry:
    """Single memory entry"""

    namespace: str
    key: str
    content: str
    metadata: Dict[str, Any]

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    accessed_at: datetime = field(default_factory=datetime.now)

    # Optional fields
    embedding: Optional[List[float]] = None
    tags: List[str] = field(default_factory=list)
    importance: float = 1.0
    decay_rate: float = 0.1

    # Entry metadata
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    version: int = 1
    checksum: Optional[str] = None


@dataclass
class MemoryResult:
    """Result from memory search"""

    content: str
    score: float
    metadata: Dict[str, Any]

    # Context info
    namespace: str
    key: str
    timestamp: datetime

    # Vector info (if applicable)
    embedding: Optional[List[float]] = None
    distance: Optional[float] = None

    # Result metadata
    result_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    rank: Optional[int] = None


@dataclass
class MemoryQuery:
    """Query for memory search"""

    query_text: str
    namespace: str

    # Search parameters
    limit: int = 10
    score_threshold: float = 0.0

    # Filters
    metadata_filters: Dict[str, Any] = field(default_factory=dict)
    tag_filters: List[str] = field(default_factory=list)
    date_range: Optional[tuple[datetime, datetime]] = None

    # Search options
    include_embeddings: bool = False
    search_type: Literal["semantic", "keyword", "hybrid"] = "semantic"

    # Query metadata
    query_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    requested_by: Optional[str] = None


# ============================================================================
# Memory Collection Types
# ============================================================================


@dataclass
class MemoryCollection:
    """Collection of related memory entries"""

    collection_id: str
    name: str
    description: str

    # Collection configuration
    max_entries: Optional[int] = None
    auto_cleanup: bool = True
    retention_days: Optional[int] = None

    # Embedding configuration
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimensions: int = 384

    # Collection metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    entry_count: int = 0
    total_size_bytes: int = 0

    # Collection settings
    settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryNamespace:
    """Namespace for organizing memory entries"""

    namespace: str
    description: str

    # Access control
    owner_agent: Optional[str] = None
    access_permissions: Dict[str, List[str]] = field(
        default_factory=dict
    )  # agent -> permissions

    # Namespace configuration
    auto_expire: bool = False
    expire_after_days: Optional[int] = None
    max_entries_per_key: int = 10

    # Statistics
    entry_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)


# ============================================================================
# Conversation Memory Types
# ============================================================================


@dataclass
class ConversationMemory:
    """Memory for conversation context"""

    conversation_id: ConversationID
    agent_id: AgentID

    # Conversation summary
    summary: str = ""
    key_points: List[str] = field(default_factory=list)

    # Message history (compressed)
    recent_messages: List[Dict[str, Any]] = field(default_factory=list)
    message_count: int = 0

    # Context tracking
    current_topics: List[str] = field(default_factory=list)
    context_switches: int = 0

    # User information learned in this conversation
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    user_goals: List[str] = field(default_factory=list)

    # Memory metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    importance_score: float = 1.0


@dataclass
class SessionMemory:
    """Temporary session-scoped memory"""

    session_id: str
    agent_id: AgentID

    # Session data
    data: Dict[str, Any] = field(default_factory=dict)

    # Session metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None

    # Session statistics
    access_count: int = 0
    size_bytes: int = 0


# ============================================================================
# Memory Analytics Types
# ============================================================================


@dataclass
class MemoryUsageStats:
    """Memory system usage statistics"""

    # Storage statistics
    total_entries: int = 0
    total_size_bytes: int = 0
    collections_count: int = 0
    namespaces_count: int = 0

    # Access patterns
    daily_reads: int = 0
    daily_writes: int = 0
    daily_searches: int = 0

    # Performance metrics
    avg_search_time_ms: float = 0.0
    avg_write_time_ms: float = 0.0
    cache_hit_rate: float = 0.0

    # Top accessed data
    top_namespaces: List[str] = field(default_factory=list)
    top_collections: List[str] = field(default_factory=list)

    # Time period
    stats_date: datetime = field(default_factory=datetime.now)
    period_hours: int = 24


@dataclass
class MemoryHealth:
    """Memory system health information"""

    # Overall health
    is_healthy: bool = True
    health_score: float = 1.0

    # Component health
    vector_store_healthy: bool = True
    kv_store_healthy: bool = True
    cache_healthy: bool = True

    # Performance indicators
    response_time_p95: float = 0.0
    error_rate: float = 0.0
    storage_utilization: float = 0.0

    # Issues
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    # Last check
    checked_at: datetime = field(default_factory=datetime.now)


# ============================================================================
# Memory Operations Types
# ============================================================================


@dataclass
class MemoryOperation:
    """Record of a memory operation"""

    operation_id: str
    operation_type: Literal["read", "write", "search", "delete", "update"]

    # Operation details
    namespace: str
    key: Optional[str] = None
    agent_id: Optional[str] = None

    # Operation results
    success: bool = True
    result_count: int = 0
    execution_time_ms: float = 0.0

    # Error information
    error_message: Optional[str] = None
    error_type: Optional[str] = None

    # Timestamps
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


@dataclass
class MemoryBatch:
    """Batch operation for multiple memory entries"""

    batch_id: str
    operation_type: Literal["bulk_insert", "bulk_update", "bulk_delete"]

    # Batch details
    namespace: str
    entry_count: int
    total_size_bytes: int = 0

    # Processing status
    status: Literal["pending", "processing", "completed", "failed"] = "pending"
    processed_count: int = 0
    failed_count: int = 0

    # Results
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# ============================================================================
# Memory Configuration Types
# ============================================================================


@dataclass
class VectorStoreConfig:
    """Configuration for vector storage backend"""

    provider: Literal["qdrant", "chroma", "pinecone", "weaviate"] = "qdrant"

    # Connection settings
    host: str = "localhost"
    port: int = 6333
    api_key: Optional[str] = None

    # Collection settings
    default_collection: str = "agent_memory"
    vector_size: int = 384
    distance_metric: Literal["cosine", "euclidean", "dot"] = "cosine"

    # Performance settings
    batch_size: int = 100
    connection_pool_size: int = 10
    timeout_seconds: int = 30

    # Provider-specific settings
    provider_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KVStoreConfig:
    """Configuration for key-value storage backend"""

    provider: Literal["redis", "sqlite", "memory"] = "redis"

    # Connection settings
    host: str = "localhost"
    port: int = 6379
    database: int = 0
    password: Optional[str] = None

    # Storage settings
    default_ttl_seconds: Optional[int] = None
    max_value_size_bytes: int = 1024 * 1024  # 1MB
    compression: bool = True

    # Performance settings
    connection_pool_size: int = 10
    timeout_seconds: int = 5

    # Provider-specific settings
    provider_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryIndexConfig:
    """Configuration for memory indexing"""

    # Index types to create
    create_text_index: bool = True
    create_metadata_index: bool = True
    create_timestamp_index: bool = True

    # Full-text search settings
    enable_fulltext_search: bool = True
    fulltext_language: str = "english"

    # Indexing performance
    background_indexing: bool = True
    index_batch_size: int = 1000

    # Index maintenance
    auto_optimize: bool = True
    optimize_frequency_hours: int = 24


# ============================================================================
# Export all memory types
# ============================================================================

__all__ = [
    # Core memory types
    "MemoryEntry",
    "MemoryResult",
    "MemoryQuery",
    # Collection types
    "MemoryCollection",
    "MemoryNamespace",
    # Conversation memory
    "ConversationMemory",
    "SessionMemory",
    # Analytics types
    "MemoryUsageStats",
    "MemoryHealth",
    # Operations types
    "MemoryOperation",
    "MemoryBatch",
    # Configuration types
    "VectorStoreConfig",
    "KVStoreConfig",
    "MemoryIndexConfig",
]
