# l6e_forge/types/core.py
"""Core data types for l6e-forge system"""

from dataclasses import dataclass, field
from typing import Any, Literal
from datetime import datetime
from pathlib import Path
import uuid

from l6e_forge.types.error import AgentError
from l6e_forge.types.tool import ToolCall


# ============================================================================
# ID Types
# ============================================================================

AgentID = uuid.UUID
ConversationID = uuid.UUID
SessionID = uuid.UUID
ModelID = uuid.UUID
ToolID = uuid.UUID
EventID = uuid.UUID
SubscriptionID = uuid.UUID
TaskID = uuid.UUID

# ============================================================================
# Core Message Types
# ============================================================================


@dataclass
class Attachment:
    """File or media attachment to a message"""

    filename: str
    content_type: str
    size_bytes: int
    url: str | None = None
    content: bytes | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Message:
    """Core message type for agent communication"""

    content: str
    role: Literal["user", "assistant", "system", "tool"]
    timestamp: datetime = field(default_factory=datetime.now)
    message_id: uuid.UUID = field(default_factory=uuid.uuid4)
    conversation_id: ConversationID = field(default_factory=uuid.uuid4)
    metadata: dict[str, Any] = field(default_factory=dict)

    # Optional fields for rich messages
    attachments: list[Attachment] = field(default_factory=list)
    tool_calls: list[ToolCall] = field(default_factory=list)  # Forward reference
    parent_message_id: uuid.UUID | None = None


@dataclass
class AgentContext:
    """Context information passed to agents"""

    conversation_id: ConversationID
    session_id: str
    user_id: str | None = None
    agent_id: AgentID | None = None
    workspace_path: Path = Path(".")
    runtime_config: dict[str, Any] = field(default_factory=dict)

    # Request context
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)

    # Session data (temporary, conversation-scoped)
    session_data: dict[str, Any] = field(default_factory=dict)

    # User preferences and settings
    user_preferences: dict[str, Any] = field(default_factory=dict)

    # Conversation history and access provider
    conversation_history: list["Message"] = field(default_factory=list)
    # TODO fix typing here to use the ConversationHistoryProvider
    history_provider: Any | None = None


@dataclass
class AgentResponse:
    """Response from an agent"""

    content: str
    agent_id: str
    response_time: float
    timestamp: datetime = field(default_factory=datetime.now)

    # Optional response data
    tool_calls: list[ToolCall] = field(default_factory=list)  # Forward reference
    metadata: dict[str, Any] = field(default_factory=dict)

    # Internal processing info
    thinking_steps: list[str] = field(default_factory=list)
    tokens_used: int | None = None
    model_used: str | None = None

    # Error information
    error: AgentError | None = None  # Forward reference
    partial_response: bool = False


# ============================================================================
# Export all types
# ============================================================================

__all__ = [
    # ID types
    "AgentID",
    "ConversationID",
    "SessionID",
    "ModelID",
    "ToolID",
    "EventID",
    "SubscriptionID",
    "TaskID",
    # Core types
    "Message",
    "Attachment",
    "AgentContext",
    "AgentResponse",
]
