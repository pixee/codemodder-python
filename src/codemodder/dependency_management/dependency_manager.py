from typing import Optional
from codemodder.change import ChangeSet
from codemodder.dependency import Dependency
from codemodder.dependency_management.requirements_txt_writer import (
    RequirementsTxtWriter,
)
from codemodder.project_analysis.file_parsers.package_store import PackageStore
from pathlib import Path


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
            case "requirements.txt":
                return RequirementsTxtWriter(
                    self.dependencies_store, self.parent_directory
                ).write(dependencies, dry_run)
            case "setup.py":
                pass
        return None
