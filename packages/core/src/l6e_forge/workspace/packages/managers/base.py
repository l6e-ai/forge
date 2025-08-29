from typing import Protocol

from l6e_forge.types.ecosystem import (
    InstallationResult,
    InstalledPackage,
    PackageSearchResult,
)


class IPackageManager(Protocol):
    """Package manager interface"""

    async def install_package(
        self, package_name: str, version: str | None = None
    ) -> InstallationResult:
        """Install a package"""
        ...

    async def uninstall_package(self, package_name: str) -> bool:
        """Uninstall a package"""
        ...

    async def update_package(self, package_name: str) -> InstallationResult:
        """Update a package to latest version"""
        ...

    def list_installed_packages(self) -> list[InstalledPackage]:
        """List installed packages"""
        ...

    async def search_packages(self, query: str) -> list[PackageSearchResult]:
        """Search for packages in registries"""
        ...
