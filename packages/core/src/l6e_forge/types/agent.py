# l6e_forge/types/agent.py
"""Agent-specific types for l6e-forge system"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from enum import Enum

from l6e_forge.types.core import AgentID, ConversationID

from .config import AgentConfig

# ============================================================================
# Agent Status and Lifecycle Types
# ============================================================================


class AgentStatus(Enum):
    """Agent lifecycle status"""

    UNLOADED = "unloaded"
    LOADING = "loading"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    STOPPING = "stopping"
    STOPPED = "stopped"


@dataclass
class AgentSpec:
    """Agent specification and metadata"""

    name: str
    path: Path
    config: AgentConfig
    module_path: str | None = None
    version: str = "1.0.0"

    # Metadata
    description: str = ""
    author: str = ""
    license: str = ""
    tags: List[str] = field(default_factory=list)

    # Runtime info
    status: AgentStatus = AgentStatus.UNLOADED
    last_loaded: Optional[datetime] = None
    load_count: int = 0
    error_count: int = 0


@dataclass
class AgentInstance:
    """Runtime agent instance"""

    agent_id: AgentID
    spec: AgentSpec
    status: AgentStatus

    # Runtime information
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)

    # Performance metrics
    total_messages_handled: int = 0
    average_response_time: float = 0.0
    success_rate: float = 1.0

    # Resource usage
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0

    # Error tracking
    recent_errors: List[str] = field(default_factory=list)
    last_error: Optional[datetime] = None


# ============================================================================
# Agent Capability Types
# ============================================================================


@dataclass
class Capability:
    """Agent capability definition"""

    name: str
    description: str
    category: str

    # Capability metadata
    version: str = "1.0.0"
    confidence: float = 1.0  # 0.0 to 1.0

    # Requirements
    required_tools: List[str] = field(default_factory=list)
    required_models: List[str] = field(default_factory=list)
    required_memory_types: List[str] = field(default_factory=list)

    # Performance characteristics
    estimated_response_time: float = 1.0  # seconds
    computational_cost: float = 1.0  # relative cost

    # Usage patterns
    common_triggers: List[str] = field(default_factory=list)
    example_inputs: List[str] = field(default_factory=list)
    example_outputs: List[str] = field(default_factory=list)


@dataclass
class AgentProfile:
    """Agent behavioral and capability profile"""

    agent_id: AgentID

    # Core capabilities
    capabilities: List[Capability] = field(default_factory=list)

    # Learned behavior patterns
    common_conversation_patterns: Dict[str, float] = field(default_factory=dict)
    preferred_tools: Dict[str, float] = field(
        default_factory=dict
    )  # tool -> usage_frequency

    # Performance characteristics
    response_time_percentiles: Dict[str, float] = field(
        default_factory=dict
    )  # p50, p95, p99
    accuracy_by_task_type: Dict[str, float] = field(default_factory=dict)

    # User interaction patterns
    user_satisfaction_scores: List[float] = field(default_factory=list)
    common_user_feedback: Dict[str, int] = field(default_factory=dict)

    # Adaptation metrics
    learning_rate: float = 0.1
    adaptation_triggers: List[str] = field(default_factory=list)

    # Last updated
    profile_updated_at: datetime = field(default_factory=datetime.now)


# ============================================================================
# Agent Communication Types
# ============================================================================


@dataclass
class AgentConversation:
    """Conversation state between user and agent"""

    conversation_id: ConversationID
    agent_id: AgentID
    user_id: Optional[str] = None

    # Conversation metadata
    started_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    message_count: int = 0

    # Conversation state
    current_context: Dict[str, Any] = field(default_factory=dict)
    conversation_summary: str = ""

    # Topics and intents
    detected_topics: List[str] = field(default_factory=list)
    current_intent: Optional[str] = None
    intent_confidence: float = 0.0

    # User preferences learned in this conversation
    learned_preferences: Dict[str, Any] = field(default_factory=dict)

    # Conversation quality metrics
    user_satisfaction: Optional[float] = None
    task_completion_rate: float = 0.0

    # Flags
    is_active: bool = True
    requires_human_handoff: bool = False


@dataclass
class AgentTeam:
    """Collection of agents working together"""

    team_id: str
    name: str
    description: str

    # Team composition
    member_agents: Dict[str, str] = field(default_factory=dict)  # agent_id -> role
    team_lead: Optional[str] = None

    # Team capabilities
    collective_capabilities: List[Capability] = field(default_factory=list)
    specialization_matrix: Dict[str, List[str]] = field(
        default_factory=dict
    )  # agent -> capabilities

    # Communication patterns
    communication_rules: Dict[str, List[str]] = field(
        default_factory=dict
    )  # agent -> can_communicate_with
    escalation_chain: List[str] = field(default_factory=list)

    # Team performance
    team_metrics: Dict[str, float] = field(default_factory=dict)
    collaboration_effectiveness: float = 1.0

    # Team state
    active_tasks: Dict[str, str] = field(
        default_factory=dict
    )  # task_id -> assigned_agent
    team_status: str = "idle"  # idle, working, coordinating, blocked

    created_at: datetime = field(default_factory=datetime.now)


# ============================================================================
# Agent Learning and Adaptation Types
# ============================================================================


@dataclass
class LearningEvent:
    """Record of an agent learning from interaction"""

    event_id: str
    agent_id: AgentID

    # Event details
    event_type: str  # "feedback", "correction", "new_pattern", etc.
    trigger: str  # What caused this learning event

    # Learning content
    previous_behavior: Dict[str, Any]
    new_behavior: Dict[str, Any]
    confidence_change: float

    # Context
    conversation_id: ConversationID
    user_feedback: Optional[str] = None
    success_metrics: Dict[str, float] = field(default_factory=dict)

    # Validation
    validated: bool = False
    validation_source: Optional[str] = None

    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AgentKnowledgeBase:
    """Agent's accumulated knowledge and patterns"""

    agent_id: AgentID

    # Factual knowledge
    facts: Dict[str, Any] = field(default_factory=dict)
    procedures: Dict[str, List[str]] = field(default_factory=dict)

    # Learned patterns
    conversation_patterns: Dict[str, float] = field(default_factory=dict)
    successful_responses: Dict[str, List[str]] = field(default_factory=dict)

    # User-specific adaptations
    user_preferences: Dict[str, Dict[str, Any]] = field(
        default_factory=dict
    )  # user_id -> preferences
    personalization_rules: Dict[str, str] = field(default_factory=dict)

    # Domain expertise
    domain_knowledge: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    expertise_levels: Dict[str, float] = field(default_factory=dict)

    # Quality metrics
    knowledge_confidence: Dict[str, float] = field(default_factory=dict)
    last_validation: Dict[str, datetime] = field(default_factory=dict)

    # Metadata
    knowledge_version: str = "1.0"
    last_updated: datetime = field(default_factory=datetime.now)


# ============================================================================
# Export all agent types
# ============================================================================

__all__ = [
    # Core agent types
    "AgentStatus",
    "AgentSpec",
    "AgentInstance",
    # Capability types
    "Capability",
    "AgentProfile",
    # Communication types
    "AgentConversation",
    "AgentTeam",
    # Learning types
    "LearningEvent",
    "AgentKnowledgeBase",
]
