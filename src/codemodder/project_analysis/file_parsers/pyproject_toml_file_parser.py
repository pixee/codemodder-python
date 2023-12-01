from codemodder.project_analysis.file_parsers.package_store import (
    PackageStore,
    FileType,
)
from pathlib import Path
import toml

from .base_parser import BaseParser


class PyprojectTomlParser(BaseParser):
    @property
    def file_type(self):
        return FileType.TOML

    def _parse_dependencies_from_toml(self, toml_data: dict):
        # todo: handle cases for
        # 1. no dependencies
        return self._parse_dependencies(toml_data["project"]["dependencies"])

    def _parse_py_versions(self, toml_data: dict) -> list:
        # todo: handle cases for
        # 1. multiple requires-python such as "">3.5.2"",  ">=3.11.1,<3.11.2"
        maybe_project = toml_data.get("project")
        maybe_python = maybe_project.get("requires-python") if maybe_project else None
        return [maybe_python] if maybe_python else []

    def _parse_file(self, file: Path):
        data = toml.load(file)
        # todo: handle no "project" in data

        return PackageStore(
            type=self.file_type,
            file=str(file),
            dependencies=set(self._parse_dependencies_from_toml(data)),
            py_versions=self._parse_py_versions(data),
        )
