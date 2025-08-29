# l6e_forge/types/testing.py
"""Testing framework types for l6e-forge"""

from dataclasses import dataclass, field
from typing import Any, Literal
from datetime import datetime
from pathlib import Path
import uuid
from l6e_forge.types.core import AgentID

# ============================================================================
# Test Definition Types
# ============================================================================


@dataclass
class TestCase:
    """Individual test case"""

    name: str
    description: str
    input_message: str

    # Expected outcomes
    expected_outputs: list[str] = field(default_factory=list)
    expected_output_patterns: list[str] = field(default_factory=list)  # Regex patterns

    # Test configuration
    setup_steps: list[str] = field(default_factory=list)
    teardown_steps: list[str] = field(default_factory=list)
    timeout: int = 30

    # Assertions
    should_call_tools: list[str] = field(default_factory=list)
    should_not_call_tools: list[str] = field(default_factory=list)
    should_access_memory: bool = False
    should_complete_successfully: bool = True

    # Test context
    conversation_context: dict[str, Any] = field(default_factory=dict)
    agent_config_overrides: dict[str, Any] = field(default_factory=dict)

    # Test metadata
    test_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tags: list[str] = field(default_factory=list)
    priority: int = 5
    category: str = "functional"

    # Test requirements
    required_tools: list[str] = field(default_factory=list)
    required_models: list[str] = field(default_factory=list)
    required_services: list[str] = field(default_factory=list)


@dataclass
class TestSuite:
    """Collection of test cases"""

    name: str
    description: str
    test_cases: list[TestCase]

    # Suite configuration
    setup_script: str | None = None
    teardown_script: str | None = None
    parallel_execution: bool = True
    max_parallel_tests: int = 4

    # Suite dependencies
    required_agents: list[str] = field(default_factory=list)
    required_models: list[str] = field(default_factory=list)
    required_tools: list[str] = field(default_factory=list)

    # Suite metadata
    suite_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    version: str = "1.0.0"
    author: str = ""
    created_at: datetime = field(default_factory=datetime.now)

    # Suite settings
    continue_on_failure: bool = True
    retry_failed_tests: bool = False
    max_retries: int = 1


@dataclass
class TestScenario:
    """Multi-step test scenario"""

    name: str
    description: str

    # Scenario steps
    steps: list[dict[str, Any]] = field(default_factory=list)

    # Scenario configuration
    step_timeout: int = 30
    total_timeout: int = 300

    # Scenario context
    shared_context: dict[str, Any] = field(default_factory=dict)

    # Scenario metadata
    scenario_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tags: list[str] = field(default_factory=list)
    complexity: Literal["simple", "medium", "complex"] = "simple"


# ============================================================================
# Test Execution Types
# ============================================================================


@dataclass
class TestEnvironment:
    """Test environment for agents"""

    environment_id: str
    workspace_path: Path
    agent_id: AgentID

    # Environment configuration
    test_config: dict[str, Any] = field(default_factory=dict)
    mock_services: dict[str, Any] = field(default_factory=dict)

    # Isolation settings
    isolated_memory: bool = True
    isolated_filesystem: bool = True
    isolated_network: bool = True

    # Environment state
    test_session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    started_at: datetime = field(default_factory=datetime.now)
    is_active: bool = False

    # Resource limits
    max_memory_mb: int = 1024
    max_execution_time: int = 300
    max_temp_files: int = 100


@dataclass
class TestExecution:
    """Record of test execution"""

    execution_id: str
    test_case: TestCase
    environment: TestEnvironment

    # Execution status
    status: Literal["pending", "running", "passed", "failed", "skipped", "error"] = (
        "pending"
    )

    # Execution timing
    started_at: datetime | None = None
    completed_at: datetime | None = None
    execution_time: float = 0.0

    # Execution results
    actual_response: str = ""
    tool_calls_made: list[str] = field(default_factory=list)
    memory_accessed: bool = False

    # Execution context
    execution_context: dict[str, Any] = field(default_factory=dict)
    agent_state_before: dict[str, Any] = field(default_factory=dict)
    agent_state_after: dict[str, Any] = field(default_factory=dict)

    # Resource usage
    memory_used_mb: float = 0.0
    cpu_time_seconds: float = 0.0


@dataclass
class TestResult:
    """Result of running a test case"""

    test_case: TestCase
    execution: TestExecution
    passed: bool

    # Result details
    assertion_results: dict[str, bool] = field(default_factory=dict)
    assertion_failures: list[str] = field(default_factory=list)

    # Failure information
    failure_reason: str | None = None
    error_message: str | None = None
    stack_trace: str | None = None

    # Performance information
    response_quality_score: float = 0.0
    performance_score: float = 0.0

    # Result metadata
    result_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)

    # Debugging information
    debug_logs: list[str] = field(default_factory=list)
    artifacts_created: list[Path] = field(default_factory=list)


@dataclass
class TestRun:
    """Complete test run session"""

    run_id: str
    suite_name: str

    # Run configuration
    test_filter: str | None = None
    tags_filter: list[str] = field(default_factory=list)
    parallel_execution: bool = True

    # Run status
    status: Literal["pending", "running", "completed", "failed", "cancelled"] = (
        "pending"
    )

    # Run timing
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None
    total_duration: float = 0.0

    # Run results
    total_tests: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    tests_skipped: int = 0
    tests_error: int = 0

    # Individual test results
    test_results: list[TestResult] = field(default_factory=list)

    # Run metadata
    initiated_by: str = "system"
    environment_info: dict[str, str] = field(default_factory=dict)
    configuration: dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Test Configuration Types
# ============================================================================


@dataclass
class TestConfig:
    """Testing framework configuration"""

    # Test discovery
    test_directories: list[Path] = field(default_factory=lambda: [Path("tests")])
    test_file_patterns: list[str] = field(
        default_factory=lambda: ["test_*.py", "*_test.py"]
    )
    test_class_patterns: list[str] = field(default_factory=lambda: ["Test*", "*Test"])

    # Test execution
    parallel_execution: bool = True
    max_parallel_tests: int = 4
    test_timeout: int = 60

    # Mocking and fixtures
    auto_mock_external_services: bool = True
    fixture_directories: list[Path] = field(default_factory=lambda: [Path("fixtures")])

    # Reporting
    generate_coverage_report: bool = True
    coverage_threshold: float = 0.8
    generate_performance_report: bool = True

    # Output configuration
    output_format: Literal["console", "junit", "json", "html"] = "console"
    output_directory: Path = Path("test_results")
    verbose_output: bool = False

    # Test environments
    test_environments: dict[str, dict[str, Any]] = field(default_factory=dict)


@dataclass
class MockConfig:
    """Configuration for mocking services"""

    mock_id: str
    service_name: str

    # Mock behavior
    mock_type: Literal["static", "dynamic", "recorded"] = "static"
    response_data: dict[str, Any] = field(default_factory=dict)

    # Mock settings
    latency_simulation: bool = False
    error_simulation: bool = False
    error_rate: float = 0.0

    # Recording settings (for recorded mocks)
    recording_path: Path | None = None
    playback_mode: Literal["strict", "fuzzy"] = "strict"


# ============================================================================
# Test Assertion Types
# ============================================================================


@dataclass
class Assertion:
    """Test assertion"""

    assertion_type: Literal[
        "response_contains",
        "response_matches",
        "response_equals",
        "tool_called",
        "tool_not_called",
        "memory_accessed",
        "response_time_under",
        "no_errors",
        "custom",
    ]

    # Assertion parameters
    expected_value: Any = None
    actual_value: Any = None
    parameters: dict[str, Any] = field(default_factory=dict)

    # Assertion result
    passed: bool = False
    error_message: str | None = None

    # Assertion metadata
    assertion_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    weight: float = 1.0  # For weighted scoring


@dataclass
class AssertionGroup:
    """Group of related assertions"""

    group_name: str
    assertions: list[Assertion]

    # Group logic
    all_must_pass: bool = True  # False = any can pass

    # Group result
    passed: bool = False
    pass_count: int = 0
    fail_count: int = 0


# ============================================================================
# Test Data Types
# ============================================================================


@dataclass
class TestData:
    """Test data for parameterized tests"""

    data_id: str
    name: str

    # Test data
    input_data: dict[str, Any]
    expected_data: dict[str, Any]

    # Data metadata
    description: str = ""
    tags: list[str] = field(default_factory=list)

    # Data source
    source: Literal["inline", "file", "database", "generated"] = "inline"
    source_location: str | None = None


@dataclass
class TestDataSet:
    """Collection of test data"""

    dataset_name: str
    test_data: list[TestData]

    # Dataset metadata
    description: str = ""
    version: str = "1.0.0"

    # Dataset configuration
    randomize_order: bool = False
    data_validation: bool = True

    # Dataset source
    source_file: Path | None = None
    last_updated: datetime = field(default_factory=datetime.now)


# ============================================================================
# Test Reporting Types
# ============================================================================


@dataclass
class TestReport:
    """Comprehensive test report"""

    report_id: str
    test_run: TestRun

    # Report summary
    summary: str = ""
    overall_status: Literal["pass", "fail", "error"] = "pass"

    # Test statistics
    total_tests: int = 0
    pass_rate: float = 0.0
    average_execution_time: float = 0.0

    # Performance analysis
    slowest_tests: list[str] = field(default_factory=list)
    memory_usage_analysis: dict[str, float] = field(default_factory=dict)

    # Coverage information
    code_coverage: float = 0.0
    coverage_details: dict[str, float] = field(default_factory=dict)

    # Failure analysis
    failure_patterns: dict[str, int] = field(default_factory=dict)
    most_common_failures: list[str] = field(default_factory=list)

    # Report metadata
    generated_at: datetime = field(default_factory=datetime.now)
    report_format: Literal["text", "html", "json", "junit"] = "text"

    # Report artifacts
    report_files: list[Path] = field(default_factory=list)
    screenshots: list[Path] = field(default_factory=list)


@dataclass
class TestMetrics:
    """Test execution metrics"""

    # Execution metrics
    total_execution_time: float = 0.0
    average_test_time: float = 0.0
    fastest_test_time: float = 0.0
    slowest_test_time: float = 0.0

    # Resource metrics
    peak_memory_usage: float = 0.0
    average_memory_usage: float = 0.0
    cpu_utilization: float = 0.0

    # Quality metrics
    assertion_density: float = 0.0  # Assertions per test
    test_coverage: float = 0.0
    failure_rate: float = 0.0

    # Trends (compared to previous runs)
    execution_time_trend: Literal["improving", "degrading", "stable"] = "stable"
    pass_rate_trend: Literal["improving", "degrading", "stable"] = "stable"

    # Metrics metadata
    metrics_period: str = "current_run"
    baseline_comparison: bool = False


# ============================================================================
# Performance Testing Types
# ============================================================================


@dataclass
class PerformanceTest:
    """Performance test specification"""

    test_name: str
    description: str
    test_scenario: TestScenario

    # Performance criteria
    max_response_time: float = 5.0  # seconds
    max_memory_usage: float = 1024.0  # MB
    min_throughput: float = 10.0  # requests per second

    # Test parameters
    concurrent_users: int = 1
    test_duration: int = 60  # seconds
    ramp_up_time: int = 10  # seconds

    # Load pattern
    load_pattern: Literal["constant", "spike", "ramp", "step"] = "constant"


@dataclass
class PerformanceResult:
    """Performance test results"""

    test_name: str

    # Performance metrics
    avg_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0
    max_response_time: float = 0.0

    # Throughput metrics
    requests_per_second: float = 0.0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0

    # Resource metrics
    peak_memory_mb: float = 0.0
    avg_cpu_percent: float = 0.0

    # Test verdict
    performance_score: float = 0.0
    meets_criteria: bool = False
    bottlenecks_identified: list[str] = field(default_factory=list)


# ============================================================================
# Export all testing types
# ============================================================================

__all__ = [
    # Test definition types
    "TestCase",
    "TestSuite",
    "TestScenario",
    # Test execution types
    "TestEnvironment",
    "TestExecution",
    "TestResult",
    "TestRun",
    # Configuration types
    "TestConfig",
    "MockConfig",
    # Assertion types
    "Assertion",
    "AssertionGroup",
    # Test data types
    "TestData",
    "TestDataSet",
    # Reporting types
    "TestReport",
    "TestMetrics",
    # Performance testing types
    "PerformanceTest",
    "PerformanceResult",
]
