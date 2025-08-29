# l6e_forge/types/model.py
"""Model and LLM types for l6e-forge system"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Literal
from datetime import datetime
import uuid

from .core import Message

# ============================================================================
# Model Specification Types
# ============================================================================


@dataclass
class ModelSpec:
    """Complete model specification"""

    model_id: str
    provider: str
    model_name: str

    # Resource requirements
    memory_requirement_gb: float
    gpu_layers: Optional[int] = None
    context_length: int = 4096

    # Capabilities
    supports_streaming: bool = True
    supports_functions: bool = False
    supports_vision: bool = False
    supports_audio: bool = False

    # Performance characteristics
    max_tokens_per_second: float = 50.0
    inference_cost_per_1k_tokens: float = 0.0

    # Metadata
    description: str = ""
    license: str = ""
    size_bytes: Optional[int] = None
    quantization: Optional[str] = None

    # Version information
    version: str = "1.0.0"
    release_date: Optional[datetime] = None

    # Provider-specific metadata
    provider_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelInstance:
    """Runtime model instance"""

    model_id: str
    spec: ModelSpec
    status: Literal["loading", "ready", "busy", "error", "unloading"]

    # Runtime info
    loaded_at: datetime
    last_used: datetime
    use_count: int = 0
    memory_usage_gb: float = 0.0

    # Performance metrics
    avg_tokens_per_second: float = 0.0
    total_tokens_generated: int = 0
    total_requests: int = 0

    # Current load
    active_requests: int = 0
    queue_length: int = 0

    # Error tracking
    error_count: int = 0
    last_error: Optional[str] = None

    # Configuration
    load_config: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Request and Response Types
# ============================================================================


@dataclass
class CompletionRequest:
    """Request for text completion"""

    prompt: str
    model_id: str

    # Generation parameters (can override model defaults)
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    stop_sequences: Optional[List[str]] = None

    # Advanced parameters
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    repetition_penalty: Optional[float] = None

    # Request metadata
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: Optional[str] = None
    conversation_id: Optional[str] = None

    # Streaming options
    stream: bool = False

    # Function calling (if supported)
    functions: Optional[List[Dict[str, Any]]] = None
    function_call: Optional[str] = None


@dataclass
class CompletionResponse:
    """Response from text completion"""

    text: str
    model_id: str
    request_id: str

    # Generation info
    tokens_generated: int
    generation_time: float
    tokens_per_second: float

    # Model info
    finish_reason: Literal[
        "completed", "max_tokens", "stop_sequence", "error", "function_call"
    ]
    prompt_tokens: int

    # Optional fields
    logprobs: Optional[List[float]] = None
    function_call: Optional[Dict[str, Any]] = None

    # Response metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Timing information
    queue_time: float = 0.0
    processing_time: float = 0.0


@dataclass
class ChatRequest:
    """Request for chat completion"""

    messages: List[Message]
    model_id: str

    # Same parameters as CompletionRequest
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    stop_sequences: Optional[List[str]] = None

    # Advanced parameters
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    repetition_penalty: Optional[float] = None

    # Request metadata
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: Optional[str] = None
    conversation_id: Optional[str] = None

    # Streaming options
    stream: bool = False

    # Function calling
    functions: Optional[List[Dict[str, Any]]] = None
    function_call: Optional[str] = None

    # Chat-specific options
    system_message: Optional[str] = None
    max_context_length: Optional[int] = None


@dataclass
class ChatResponse:
    """Response from chat completion"""

    message: Message
    model_id: str
    request_id: str

    # Same info as CompletionResponse
    tokens_generated: int
    generation_time: float
    tokens_per_second: float
    finish_reason: Literal[
        "completed", "max_tokens", "stop_sequence", "error", "function_call"
    ]
    prompt_tokens: int

    # Chat-specific info
    context_used: int  # Number of context messages used
    context_truncated: bool = False

    # Optional fields
    logprobs: Optional[List[float]] = None
    function_call: Optional[Dict[str, Any]] = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    # Timing information
    queue_time: float = 0.0
    processing_time: float = 0.0


@dataclass
class StreamingChunk:
    """Chunk from streaming response"""

    content: str
    request_id: str
    chunk_id: int

    # Chunk metadata
    is_complete: bool = False
    token_count: int = 1

    # Optional fields
    logprobs: Optional[List[float]] = None
    function_call_delta: Optional[Dict[str, Any]] = None

    timestamp: datetime = field(default_factory=datetime.now)


# ============================================================================
# Model Provider Types
# ============================================================================


@dataclass
class ProviderConfig:
    """Configuration for a model provider"""

    provider_name: str
    provider_type: Literal["local", "api", "hybrid"]

    # Connection settings
    endpoint: Optional[str] = None
    api_key: Optional[str] = None
    timeout: int = 300

    # Authentication
    auth_method: Optional[Literal["api_key", "oauth", "basic"]] = None
    auth_config: Dict[str, Any] = field(default_factory=dict)

    # Rate limiting
    max_requests_per_minute: int = 60
    max_tokens_per_minute: int = 150000

    # Provider-specific settings
    provider_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderStatus:
    """Status of a model provider"""

    provider_name: str
    is_available: bool

    # Health information
    last_health_check: datetime
    response_time: float
    error_rate: float

    # Capacity information
    available_models: List[str]
    current_load: float  # 0.0 to 1.0
    queue_length: int

    # Error information
    recent_errors: List[str] = field(default_factory=list)
    last_error: Optional[str] = None


# ============================================================================
# Model Performance and Analytics
# ============================================================================


@dataclass
class ModelPerformanceMetrics:
    """Performance metrics for a model"""

    model_id: str

    # Usage statistics
    total_requests: int = 0
    total_tokens_generated: int = 0
    total_inference_time: float = 0.0

    # Performance metrics
    avg_tokens_per_second: float = 0.0
    avg_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0

    # Quality metrics
    success_rate: float = 1.0
    error_rate: float = 0.0
    timeout_rate: float = 0.0

    # Resource utilization
    avg_memory_usage: float = 0.0
    peak_memory_usage: float = 0.0
    avg_gpu_utilization: float = 0.0

    # Cost metrics (if applicable)
    total_cost: float = 0.0
    cost_per_1k_tokens: float = 0.0

    # Time period for these metrics
    period_start: datetime = field(default_factory=datetime.now)
    period_end: datetime = field(default_factory=datetime.now)


@dataclass
class ModelUsagePattern:
    """Usage pattern analysis for a model"""

    model_id: str

    # Temporal patterns
    hourly_usage: Dict[int, int] = field(default_factory=dict)  # hour -> request_count
    daily_usage: Dict[str, int] = field(default_factory=dict)  # day -> request_count

    # Request characteristics
    avg_prompt_length: float = 0.0
    avg_completion_length: float = 0.0
    common_parameters: Dict[str, Any] = field(default_factory=dict)

    # User patterns
    top_agents: List[str] = field(default_factory=list)
    agent_usage_distribution: Dict[str, float] = field(default_factory=dict)

    # Performance patterns
    peak_load_hours: List[int] = field(default_factory=list)
    performance_by_hour: Dict[int, float] = field(default_factory=dict)

    # Analysis metadata
    analysis_period_days: int = 7
    last_updated: datetime = field(default_factory=datetime.now)


# ============================================================================
# Model Management Types
# ============================================================================


@dataclass
class ModelLoadRequest:
    """Request to load a model"""

    model_spec: ModelSpec
    load_config: Dict[str, Any] = field(default_factory=dict)

    # Loading options
    priority: int = 5  # 1-10, lower = higher priority
    force_reload: bool = False

    # Resource constraints
    max_memory_gb: Optional[float] = None
    max_gpu_layers: Optional[int] = None

    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    requested_by: Optional[str] = None
    requested_at: datetime = field(default_factory=datetime.now)


@dataclass
class ModelUnloadRequest:
    """Request to unload a model"""

    model_id: str

    # Unloading options
    force: bool = False
    save_state: bool = True

    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    requested_by: Optional[str] = None
    requested_at: datetime = field(default_factory=datetime.now)


@dataclass
class ModelOptimizationConfig:
    """Configuration for model optimization"""

    # Quantization settings
    enable_quantization: bool = True
    quantization_method: Literal["int8", "int4", "fp16"] = "int8"

    # Memory optimization
    enable_memory_mapping: bool = True
    enable_kv_cache_optimization: bool = True
    max_kv_cache_size_gb: float = 4.0

    # Inference optimization
    batch_size: int = 1
    max_batch_size: int = 8
    enable_dynamic_batching: bool = False

    # Hardware optimization
    use_gpu: bool = True
    gpu_layers: Optional[int] = None
    use_mlock: bool = False


# ============================================================================
# Export all model types
# ============================================================================

__all__ = [
    # Model specification
    "ModelSpec",
    "ModelInstance",
    # Request/Response types
    "CompletionRequest",
    "CompletionResponse",
    "ChatRequest",
    "ChatResponse",
    "StreamingChunk",
    # Provider types
    "ProviderConfig",
    "ProviderStatus",
    # Performance types
    "ModelPerformanceMetrics",
    "ModelUsagePattern",
    # Management types
    "ModelLoadRequest",
    "ModelUnloadRequest",
    "ModelOptimizationConfig",
]
