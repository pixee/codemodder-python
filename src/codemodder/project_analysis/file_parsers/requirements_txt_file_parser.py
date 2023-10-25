from codemodder.project_analysis.file_parsers.package_store import PackageStore
from packaging.requirements import Requirement
from pathlib import Path
from typing import List
from .base_parser import BaseParser


class RequirementsTxtParser(BaseParser):
    def __init__(self, parent_directory: Path):
        super().__init__(parent_directory)
        self.file_name = "requirements.txt"

    def _parse_file(self, file: Path):
        with open(file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        return PackageStore(
            type=self.file_name,
            file=str(file),
            dependencies=self._parse_dependencies(lines),
            # requirements.txt files do not declare py versions explicitly
            # though we could create a heuristic by analyzing each dependency
            # and extracting py versions from them.
            py_versions=[],
        )
