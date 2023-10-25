from codemodder.project_analysis.file_parsers.package_store import PackageStore
from pathlib import Path
import toml

from .base_parser import BaseParser


class PyprojectTomlParser(BaseParser):
    @property
    def file_name(self):
        return "pyproject.toml"

    def _parse_dependencies_from_toml(self, toml_data: dict):
        # todo: handle cases for
        # 1. no dependencies
        return self._parse_dependencies(toml_data["project"]["dependencies"])

    def _parse_py_versions(self, toml_data: dict):
        # todo: handle cases for
        # 1. no requires-python
        # 2. multiple requires-python such as "">3.5.2"",  ">=3.11.1,<3.11.2"
        return [toml_data["project"]["requires-python"]]

    def _parse_file(self, file: Path):
        data = toml.load(file)
        # todo: handle no "project" in data

        return PackageStore(
            type=self.file_name,
            file=str(file),
            dependencies=self._parse_dependencies_from_toml(data),
            py_versions=self._parse_py_versions(data),
        )
