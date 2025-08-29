from pathlib import Path
from typing import Protocol

from l6e_forge.types.testing import (
    TestCase,
    TestEnvironment,
    TestResult,
    TestRun,
    TestSuite,
)


class ITestRunner(Protocol):
    """Test runner interface"""

    async def discover_tests(self, test_path: Path) -> list[TestCase]:
        """Discover test cases in the given path"""
        ...

    async def run_test(
        self, test_case: TestCase, environment: TestEnvironment
    ) -> TestResult:
        """Run a single test case"""
        ...

    async def run_test_suite(self, test_suite: TestSuite) -> TestRun:
        """Run a test suite"""
        ...

    def get_test_results(self, run_id: str) -> TestRun:
        """Get test results by run ID"""
        ...
