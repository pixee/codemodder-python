from pathlib import Path

import toml

from codemodder.project_analysis.file_parsers.package_store import (
    FileType,
    PackageStore,
)

from .base_parser import BaseParser


class PyprojectTomlParser(BaseParser):
    @property
    def file_type(self):
        return FileType.TOML

    def _parse_file(self, file: Path) -> PackageStore | None:
        """
        Parse a pyproject.toml file which may or may not use poetry.
        """
        data = toml.load(file)
        project_data = data.get("project")
        poetry_data = data.get("tool", {}).get("poetry")

        if not project_data and not poetry_data:
            return None

        version = None
        project_dependencies, poetry_dependencies = [], []
        if project_data:
            project_dependencies = project_data.get("dependencies", [])
            version = project_data.get("requires-python", None)

        if poetry_data:
            poetry_dependencies = [
                f"{name}{version}"
                for name, version in poetry_data.get("dependencies", {}).items()
                if name != "python"
            ]

            # In poetry python version is declared within `[tool.poetry.dependencies]`
            version = poetry_data.get("dependencies", {}).get("python", None)

        return PackageStore(
            type=self.file_type,
            file=file,
            dependencies=set(project_dependencies + poetry_dependencies),
            py_versions=[version] if version else [],
        )
