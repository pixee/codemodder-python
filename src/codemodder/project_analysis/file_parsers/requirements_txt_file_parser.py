from codemodder.project_analysis.file_parsers.package_store import PackageStore
from pathlib import Path
from .base_parser import BaseParser


class RequirementsTxtParser(BaseParser):
    @property
    def file_name(self):
        return "requirements.txt"

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
