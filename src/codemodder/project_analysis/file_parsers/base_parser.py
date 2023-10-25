from abc import ABC, abstractmethod

from pathlib import Path
from typing import List
from .package_store import PackageStore
from packaging.requirements import Requirement


class BaseParser(ABC):
    def __init__(self, parent_directory: Path):
        self.parent_directory = parent_directory

    @property
    @abstractmethod
    def file_name(self):
        ...  # pragma: no cover

    def _parse_dependencies(self, dependencies: List[str]):
        return [
            Requirement(line)
            for x in dependencies
            # Skip empty lines and comments
            if (line := x.strip()) and not line.startswith("#")
        ]

    @abstractmethod
    def _parse_file(self, file: Path):
        ...  # pragma: no cover

    def find_file_locations(self) -> List[Path]:
        return list(Path(self.parent_directory).rglob(self.file_name))

    def parse(self) -> list[PackageStore]:
        """
        Find 0 or more project config or dependency files within a project repo.
        """
        stores = []
        req_files = self.find_file_locations()
        for file in req_files:
            store = self._parse_file(file)
            stores.append(store)
        return stores
