from functools import cached_property
from pathlib import Path
from typing import Optional

from packaging.requirements import Requirement

from codemodder.change import Action, Change, ChangeSet, PackageAction, Result
from codemodder.diff import create_diff
from codemodder.dependency import Dependency


class DependencyManager:
    parent_directory: Path
    _lines: list[str]
    _new_requirements: list[Dependency]

    def __init__(self, parent_directory: Path):
        self.parent_directory = parent_directory
        self.dependency_file_changed = False
        self._lines = []
        self._new_requirements = []

    @property
    def new_requirements(self) -> list[str]:
        return [str(x.requirement) for x in self._new_requirements]

    def add(self, dependencies: list[Dependency]):
        """add any number of dependencies to the end of list of dependencies."""
        for dep in dependencies:
            if dep.requirement.name not in self.dependencies:
                self.dependencies.update({dep.requirement.name: dep.requirement})
                self._new_requirements.append(dep)

    def write(self, dry_run: bool = False) -> Optional[ChangeSet]:
        """
        Write the updated dependency files if any changes were made.
        """
        if not (self.dependency_file and self._new_requirements):
            return None

        original_lines = self._lines.copy()
        if not original_lines[-1].endswith("\n"):
            original_lines[-1] += "\n"

        requirement_lines = [f"{req}\n" for req in self.new_requirements]

        updated = original_lines + requirement_lines
        diff = create_diff(self._lines, updated)

        changes = [
            Change(
                lineNumber=len(original_lines) + i + 1,
                description=dep.build_description(),
                # Contextual comments should be added to the right side of split diffs
                properties={
                    "contextual_description": True,
                    "contextual_description_position": "right",
                },
                packageActions=[
                    PackageAction(Action.ADD, Result.COMPLETED, str(dep.requirement))
                ],
            )
            for i, dep in enumerate(self._new_requirements)
        ]

        if not dry_run:
            with open(self.dependency_file, "w", encoding="utf-8") as f:
                f.writelines(original_lines)
                f.writelines(requirement_lines)

        self.dependency_file_changed = True
        return ChangeSet(
            str(self.dependency_file.relative_to(self.parent_directory)),
            diff,
            changes=changes,
        )

    @property
    def found_dependency_file(self) -> bool:
        return self.dependency_file is not None

    @cached_property
    def dependency_file(self) -> Optional[Path]:
        try:
            # For now for simplicity only return the first file
            return next(Path(self.parent_directory).rglob("requirements.txt"))
        except StopIteration:
            pass
        return None

    @cached_property
    def dependencies(self) -> dict[str, Requirement]:
        """
        Extract list of dependencies from requirements.txt file.
        Same order of requirements is maintained, no alphabetical sorting is done.
        """
        if not self.dependency_file:
            return {}

        with open(self.dependency_file, "r", encoding="utf-8") as f:
            self._lines = f.readlines()

        return {
            requirement.name: requirement
            for x in self._lines
            # Skip empty lines and comments
            if (line := x.strip())
            and not line.startswith("#")
            and (requirement := Requirement(line))
        }
