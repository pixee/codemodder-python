from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from codemodder.logging import logger

from .package_store import FileType, PackageStore


class BaseParser(ABC):
    parent_directory: Path

    def __init__(self, parent_directory: Path):
        self.parent_directory = parent_directory

    @property
    @abstractmethod
    def file_type(self) -> FileType:
        pass

    @abstractmethod
    def _parse_file(self, file: Path) -> PackageStore | None:
        pass

    def find_file_locations(self) -> List[Path]:
        return list(Path(self.parent_directory).rglob(self.file_type.value))

    def parse(self) -> list[PackageStore]:
        """
        Find 0 or more project config or dependency files within a project repo.
        """
        stores = []
        req_files = self.find_file_locations()
        for file in req_files:
            try:
                store = self._parse_file(file)
            except Exception as e:
                logger.debug("Error parsing file: %s", file, exc_info=e)
                continue

            if store:
                stores.append(store)
        return stores
