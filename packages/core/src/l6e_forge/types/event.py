# l6e_forge/types/event.py
"""Event system types for l6e-forge"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Literal, Callable, Union
from datetime import datetime
import uuid

# ============================================================================
# Core Event Types
# ============================================================================


@dataclass
class Event:
    """System event for inter-agent communication"""

    event_type: str
    payload: Dict[str, Any]

    # Identity
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)

    # Routing
    source_agent_id: Optional[str] = None
    target_agent_id: Optional[str] = None
    conversation_id: Optional[str] = None  # JSON boundary: keep string here

    # Event metadata
    priority: int = 5  # 1-10, lower = higher priority
    ttl: Optional[int] = None  # seconds
    retry_count: int = 0
    max_retries: int = 3

    # Correlation
    correlation_id: Optional[str] = None
    parent_event_id: Optional[str] = None

    # Processing info
    processed: bool = False
    processed_at: Optional[datetime] = None
    processing_duration: float = 0.0


# Type alias for event handlers
EventHandler = Callable[[Event], Union[None, bool]]  # Return False to stop propagation
AsyncEventHandler = Callable[[Event], Union[None, bool]]


@dataclass
class EventSubscription:
    """Event subscription record"""

    subscription_id: str
    event_type: str
    handler: Union[EventHandler, AsyncEventHandler]

    # Subscription details
    subscriber_id: str  # Usually agent_id
    priority: int = 5

    # Filtering
    filter_conditions: Dict[str, Any] = field(default_factory=dict)
    source_filter: Optional[str] = None  # Filter by source agent

    # Subscription metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0

    # Subscription settings
    auto_unsubscribe_after: Optional[int] = None  # Unsubscribe after N triggers
    expires_at: Optional[datetime] = None


# ============================================================================
# Event Bus Types
# ============================================================================


@dataclass
class EventBusConfig:
    """Configuration for the event bus"""

    # Bus settings
    max_queue_size: int = 10000
    max_concurrent_handlers: int = 100
    default_timeout: int = 30

    # Persistence settings
    persist_events: bool = True
    event_history_limit: int = 100000
    cleanup_interval_hours: int = 24

    # Performance settings
    batch_processing: bool = True
    batch_size: int = 100
    enable_async_handlers: bool = True

    # Dead letter queue
    enable_dlq: bool = True
    dlq_max_retries: int = 3
    dlq_retry_delay: int = 60  # seconds


@dataclass
class EventRoute:
    """Event routing rule"""

    route_id: str
    name: str
    description: str

    # Routing conditions
    event_type_pattern: str  # Regex pattern
    source_conditions: Dict[str, Any] = field(default_factory=dict)
    payload_conditions: Dict[str, Any] = field(default_factory=dict)

    # Routing actions
    target_agents: List[str] = field(default_factory=list)
    target_event_types: List[str] = field(default_factory=list)

    # Transform payload
    payload_transform: Optional[str] = None  # Python expression

    # Route metadata
    priority: int = 5
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)

    # Statistics
    match_count: int = 0
    last_matched: Optional[datetime] = None


# ============================================================================
# Standard Event Types
# ============================================================================


@dataclass
class AgentEvent(Event):
    """Base class for agent-related events"""

    def __init__(self, event_type: str, agent_id: str, **kwargs):
        super().__init__(event_type=event_type, **kwargs)
        self.source_agent_id = agent_id
        self.payload["agent_id"] = agent_id


@dataclass
class ConversationEvent(Event):
    """Base class for conversation-related events"""

    def __init__(self, event_type: str, conversation_id: str, **kwargs):
        super().__init__(event_type=event_type, **kwargs)
        self.conversation_id = conversation_id
        self.payload["conversation_id"] = conversation_id


@dataclass
class SystemEvent(Event):
    """Base class for system-level events"""

    def __init__(self, event_type: str, component: str, **kwargs):
        super().__init__(event_type=event_type, **kwargs)
        self.payload["component"] = component


# ============================================================================
# Event Processing Types
# ============================================================================


@dataclass
class EventProcessingResult:
    """Result of processing an event"""

    event_id: str
    success: bool

    # Processing details
    handlers_called: int = 0
    handlers_succeeded: int = 0
    handlers_failed: int = 0

    # Timing
    processing_time: float = 0.0
    queue_time: float = 0.0

    # Errors
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Results from handlers
    handler_results: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EventBatch:
    """Batch of events for processing"""

    batch_id: str
    events: List[Event]

    # Batch metadata
    created_at: datetime = field(default_factory=datetime.now)
    batch_size: int = 0

    # Processing status
    status: Literal["pending", "processing", "completed", "failed"] = "pending"
    processed_count: int = 0
    failed_count: int = 0

    # Results
    results: List[EventProcessingResult] = field(default_factory=list)

    def __post_init__(self):
        self.batch_size = len(self.events)


@dataclass
class EventQueue:
    """Event queue for ordered processing"""

    queue_id: str
    name: str

    # Queue configuration
    max_size: int = 1000
    fifo: bool = True  # False for priority queue

    # Queue state
    current_size: int = 0
    processed_count: int = 0
    failed_count: int = 0

    # Processing settings
    consumer_count: int = 1
    batch_processing: bool = False
    batch_size: int = 10

    # Queue metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_processed: Optional[datetime] = None


# ============================================================================
# Event Analytics Types
# ============================================================================


@dataclass
class EventStats:
    """Event system statistics"""

    # Event counts
    total_events: int = 0
    events_processed: int = 0
    events_failed: int = 0
    events_pending: int = 0

    # Event types
    event_type_distribution: Dict[str, int] = field(default_factory=dict)
    top_event_types: List[str] = field(default_factory=list)

    # Performance metrics
    avg_processing_time: float = 0.0
    avg_queue_time: float = 0.0
    throughput_events_per_second: float = 0.0

    # Agent activity
    most_active_publishers: List[str] = field(default_factory=list)
    most_active_subscribers: List[str] = field(default_factory=list)

    # Time period
    stats_period_start: datetime = field(default_factory=datetime.now)
    stats_period_end: datetime = field(default_factory=datetime.now)


@dataclass
class EventTrace:
    """Trace of event processing"""

    trace_id: str
    event_id: str

    # Trace steps
    steps: List[Dict[str, Any]] = field(default_factory=list)

    # Trace metadata
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    total_duration: float = 0.0

    # Trace context
    correlation_id: Optional[str] = None
    trace_parent: Optional[str] = None


# ============================================================================
# Event Pattern Types
# ============================================================================


@dataclass
class EventPattern:
    """Pattern for complex event processing"""

    pattern_id: str
    name: str
    description: str

    # Pattern definition
    event_sequence: List[str] = field(default_factory=list)  # Event types in order
    time_window: Optional[int] = None  # Seconds

    # Pattern conditions
    conditions: Dict[str, Any] = field(default_factory=dict)
    min_occurrences: int = 1
    max_occurrences: Optional[int] = None

    # Pattern actions
    action_type: Literal["emit_event", "call_handler", "notify"] = "emit_event"
    action_config: Dict[str, Any] = field(default_factory=dict)

    # Pattern metadata
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)

    # Pattern statistics
    match_count: int = 0
    last_matched: Optional[datetime] = None


@dataclass
class EventCorrelation:
    """Correlation between related events"""

    correlation_id: str

    # Correlated events
    event_ids: List[str] = field(default_factory=list)
    event_chain: List[str] = field(default_factory=list)  # Ordered sequence

    # Correlation metadata
    correlation_type: str = "sequence"  # sequence, scatter-gather, etc.
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    # Correlation state
    is_complete: bool = False
    expected_events: int = 0
    received_events: int = 0

    # Results
    correlation_result: Optional[Dict[str, Any]] = None


# ============================================================================
# Event Middleware Types
# ============================================================================


@dataclass
class EventMiddleware:
    """Middleware for event processing"""

    middleware_id: str
    name: str

    # Middleware configuration
    order: int = 100  # Lower numbers execute first
    event_types: List[str] = field(default_factory=list)  # Empty = all events

    # Processing hooks
    pre_process: Optional[Callable[[Event], Event]] = None
    post_process: Optional[Callable[[Event, EventProcessingResult], None]] = None

    # Middleware settings
    enabled: bool = True
    async_processing: bool = False

    # Middleware metadata
    created_at: datetime = field(default_factory=datetime.now)
    execution_count: int = 0


@dataclass
class EventFilter:
    """Filter for event processing"""

    filter_id: str
    name: str

    # Filter conditions
    event_type_patterns: List[str] = field(default_factory=list)
    source_agents: List[str] = field(default_factory=list)
    payload_conditions: Dict[str, Any] = field(default_factory=dict)

    # Filter action
    action: Literal["allow", "deny", "transform"] = "allow"
    transform_config: Dict[str, Any] = field(default_factory=dict)

    # Filter metadata
    enabled: bool = True
    priority: int = 5

    # Filter statistics
    events_processed: int = 0
    events_filtered: int = 0


# ============================================================================
# Export all event types
# ============================================================================

__all__ = [
    # Core event types
    "Event",
    "EventHandler",
    "AsyncEventHandler",
    "EventSubscription",
    # Event bus types
    "EventBusConfig",
    "EventRoute",
    # Standard event types
    "AgentEvent",
    "ConversationEvent",
    "SystemEvent",
    # Processing types
    "EventProcessingResult",
    "EventBatch",
    "EventQueue",
    # Analytics types
    "EventStats",
    "EventTrace",
    # Pattern types
    "EventPattern",
    "EventCorrelation",
    # Middleware types
    "EventMiddleware",
    "EventFilter",
]
