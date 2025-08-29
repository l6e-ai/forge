from typing import Protocol

from l6e_forge.types.ecosystem import (
    AgentPackage,
    AgentPackageMetadata,
    PackageSearchResult,
    PublishingResult,
)


class IPackageRegistry(Protocol):
    """Package registry interface"""

    async def search(self, query: str) -> list[PackageSearchResult]:
        """Search packages in this registry"""
        ...

    async def get_package_info(self, package_name: str) -> AgentPackageMetadata:
        """Get package metadata"""
        ...

    async def download_package(self, package_name: str, version: str) -> bytes:
        """Download a package"""
        ...

    async def upload_package(self, package: AgentPackage) -> PublishingResult:
        """Upload a package to registry"""
        ...
