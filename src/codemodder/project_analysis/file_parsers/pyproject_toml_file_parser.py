from pathlib import Path

import toml

from codemodder.project_analysis.file_parsers.package_store import (
    PackageStore,
    FileType,
)
from .base_parser import BaseParser


class PyprojectTomlParser(BaseParser):
    @property
    def file_type(self):
        return FileType.TOML

    def _parse_file(self, file: Path) -> PackageStore | None:
        data = toml.load(file)

        if not (project := data.get("project")):
            return None

        dependencies = project.get("dependencies", [])
        version = project.get("requires-python", None)

        return PackageStore(
            type=self.file_type,
            file=file,
            dependencies=set(dependencies),
            py_versions=[version] if version else [],
        )
