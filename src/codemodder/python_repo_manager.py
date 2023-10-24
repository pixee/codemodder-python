from functools import cached_property
from pathlib import Path
from codemodder.file_parsers import RequirementsTxtParser
from codemodder.file_parsers.package_store import PackageStore


class PythonRepoManager:
    def __init__(self, parent_directory: Path):
        self.parent_directory = parent_directory
        self._potential_stores = [RequirementsTxtParser]

    @cached_property
    def package_stores(self) -> list[PackageStore]:
        return self._parse_all_stores()

    def _parse_all_stores(self) -> list[PackageStore]:
        discovered_pkg_stores: list[PackageStore] = []
        for store in self._potential_stores:
            discovered_pkg_stores.extend(store(self.parent_directory).parse())
        return discovered_pkg_stores
