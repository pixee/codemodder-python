from pathlib import Path
from typing import Optional

from codemodder.codetf import ChangeSet
from codemodder.dependency import Dependency
from codemodder.dependency_management.pyproject_writer import PyprojectWriter
from codemodder.dependency_management.requirements_txt_writer import (
    RequirementsTxtWriter,
)
from codemodder.dependency_management.setup_py_writer import SetupPyWriter
from codemodder.dependency_management.setupcfg_writer import SetupCfgWriter
from codemodder.project_analysis.file_parsers.package_store import (
    FileType,
    PackageStore,
)


class DependencyManager:
    dependencies_store: PackageStore
    parent_directory: Path

    def __init__(self, dependencies_store: PackageStore, parent_directory: Path):
        self.dependencies_store = dependencies_store
        self.parent_directory = parent_directory

    def write(
        self, dependencies: list[Dependency], dry_run: bool = False
    ) -> Optional[ChangeSet]:
        """
        Write `dependencies` to the appropriate location in the project.
        """
        match self.dependencies_store.type:
            case FileType.REQ_TXT:
                return RequirementsTxtWriter(
                    self.dependencies_store, self.parent_directory
                ).write(dependencies, dry_run)
            case FileType.TOML:
                return PyprojectWriter(
                    self.dependencies_store, self.parent_directory
                ).write(dependencies, dry_run)
            case FileType.SETUP_PY:
                return SetupPyWriter(
                    self.dependencies_store, self.parent_directory
                ).write(dependencies, dry_run)
            case FileType.SETUP_CFG:
                return SetupCfgWriter(
                    self.dependencies_store, self.parent_directory
                ).write(dependencies, dry_run)
        return None
