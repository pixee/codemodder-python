from codemodder.file_parsers.package_store import PackageStore
from packaging.requirements import Requirement
from pathlib import Path
from typing import List


class RequirementsTxtParser:
    def __init__(self, parent_directory: Path):
        self.parent_directory = parent_directory
        self.file_name = "requirements.txt"

    def find_file_locations(self) -> List[Path]:
        return list(Path(self.parent_directory).rglob(self.file_name))

    def _parse_dependencies(self, lines: List[str]):
        return [
            Requirement(line)
            for x in lines
            # Skip empty lines and comments
            if (line := x.strip()) and not line.startswith("#")
        ]

    def _parse_file(self, file: Path):
        with open(file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        return PackageStore(
            type="requirements_txt",
            file=str(file),
            dependencies=self._parse_dependencies(lines),
            # requirements.txt files do not declare py versions explicitly
            # though we could create a heuristic by analyzing each dependency
            # and extracting py versions from them.
            py_versions=[],
        )

    def parse(self) -> list[PackageStore]:
        """
        Find 0 or more requirements.txt files within a project repo.
        """
        stores = []
        req_files = self.find_file_locations()
        for file in req_files:
            store = self._parse_file(file)
            stores.append(store)
        return stores
