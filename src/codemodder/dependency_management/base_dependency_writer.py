from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import Callable, List, Optional, Union

from packaging.requirements import Requirement

from codemodder.codetf import Action, Change, ChangeSet, PackageAction, PackageResult
from codemodder.dependency import Dependency
from codemodder.project_analysis.file_parsers.package_store import PackageStore


class DependencyWriter(metaclass=ABCMeta):
    dependency_store: PackageStore

    def __init__(self, dependency_store: PackageStore, parent_directory: Path):
        self.dependency_store = dependency_store
        self.path = Path(dependency_store.file)
        self.parent_directory = parent_directory

    @abstractmethod
    def add_to_file(
        self, dependencies: list[Dependency], dry_run: bool = False
    ) -> Optional[ChangeSet]:
        pass

    def write(
        self, dependencies: list[Dependency], dry_run: bool = False
    ) -> Optional[ChangeSet]:
        if new_dependencies := self.add(dependencies):
            return self.add_to_file(new_dependencies, dry_run)
        return None

    def add(self, dependencies: list[Dependency]) -> list[Dependency]:
        """add any number of dependencies to the end of list of dependencies."""
        new = []

        for new_dep in dependencies:
            requirement: Requirement = new_dep.requirement
            if not self.dependency_store.has_requirement(requirement):
                self.dependency_store.dependencies.add(requirement)
                new.append(new_dep)
        return new

    def build_changes(
        self,
        dependencies: list[Dependency],
        line_number_strategy: Callable,
        strategy_arg: Union[int, List[str], List[int]],
    ) -> list[Change]:
        return [
            Change(
                lineNumber=line_number_strategy(strategy_arg, i),
                description=dep.build_description(),
                # Contextual comments should be added to the right side of split diffs
                properties={
                    "contextual_description": True,
                    # TODO: `contextual_description_position` is deprecated in
                    # favor of Change.diffSide.
                    # We're keeping it here for backwards compatibility but it
                    # should eventually be removed.
                    "contextual_description_position": "right",
                },
                packageActions=[
                    PackageAction(
                        action=Action.ADD,
                        result=PackageResult.COMPLETED,
                        package=str(dep.requirement),
                    )
                ],
            )
            for i, dep in enumerate(dependencies)
        ]
