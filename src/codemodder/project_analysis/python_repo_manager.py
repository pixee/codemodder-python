from functools import cached_property
from pathlib import Path
from typing import Optional

from codemodder.project_analysis.file_parsers import (
    PyprojectTomlParser,
    RequirementsTxtParser,
    SetupCfgParser,
    SetupPyParser,
)
from codemodder.project_analysis.file_parsers.package_store import PackageStore


class PythonRepoManager:
    def __init__(self, parent_directory: Path):
        self.parent_directory = parent_directory
        self._potential_stores = [
            PyprojectTomlParser,
            SetupPyParser,
            RequirementsTxtParser,
            SetupCfgParser,
        ]

    @cached_property
    def dependencies_store(self) -> Optional[PackageStore]:
        """The location where to write new dependencies for project.
        For now just pick the first store found with order given by _potential_stores.
        """
        if self.package_stores:
            return self.package_stores[0]
        return None

    @cached_property
    def package_stores(self) -> list[PackageStore]:
        return self._parse_all_stores()

    def parse_project(self) -> list[PackageStore]:
        """Wrapper around cached-property for clarity when calling it the first time."""
        return self.package_stores

    def _parse_all_stores(self) -> list[PackageStore]:
        discovered_pkg_stores: list[PackageStore] = []
        for store in self._potential_stores:
            discovered_pkg_stores.extend(
                store(self.parent_directory).parse()  # type: ignore
            )
        return discovered_pkg_stores
