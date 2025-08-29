from typing import Protocol

from l6e_forge.core.agents.base import IAgent


class ITestEnvironment(Protocol):
    """Test environment interface"""

    async def setup(self) -> None:
        """Set up the test environment"""
        ...

    async def teardown(self) -> None:
        """Tear down the test environment"""
        ...

    async def reset(self) -> None:
        """Reset environment to clean state"""
        ...

    def get_agent(self) -> IAgent:
        """Get the agent under test"""
        ...
