from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import Optional
from codemodder.project_analysis.file_parsers.package_store import PackageStore
from codemodder.change import ChangeSet
from codemodder.dependency import Dependency
from packaging.requirements import Requirement


class DependencyWriter(metaclass=ABCMeta):
    dependency_store: PackageStore

    def __init__(self, dependency_store: PackageStore, parent_directory: Path):
        self.dependency_store = dependency_store
        self.path = Path(dependency_store.file)
        self.parent_directory = parent_directory

    @abstractmethod
    def write(
        self, dependencies: list[Dependency], dry_run: bool = False
    ) -> Optional[ChangeSet]:
        pass

    def add(self, dependencies: list[Dependency]) -> Optional[list[Dependency]]:
        """add any number of dependencies to the end of list of dependencies."""
        new = []
        for new_dep in dependencies:
            requirement: Requirement = new_dep.requirement
            if requirement not in self.dependency_store.dependencies:
                self.dependency_store.dependencies.append(requirement)
                new.append(new_dep)
        return new
