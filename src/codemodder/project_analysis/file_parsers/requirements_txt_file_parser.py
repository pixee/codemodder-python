from codemodder.project_analysis.file_parsers.package_store import (
    PackageStore,
    FileType,
)
from pathlib import Path
from .base_parser import BaseParser


class RequirementsTxtParser(BaseParser):
    @property
    def file_type(self):
        return FileType.REQ_TXT

    def _parse_file(self, file: Path):
        with open(file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        return PackageStore(
            type=self.file_type,
            file=str(file),
            dependencies=set(self._parse_dependencies(lines)),
            # requirements.txt files do not declare py versions explicitly
            # though we could create a heuristic by analyzing each dependency
            # and extracting py versions from them.
            py_versions=[],
        )
