from functools import cached_property
from pathlib import Path
from typing import Optional

import difflib
from packaging.requirements import Requirement

from codemodder.change import ChangeSet


class DependencyManager:
    parent_directory: Path
    _lines: list[str]
    _new_requirements: list[str]

    def __init__(self, parent_directory: Path):
        """One-time class initialization."""
        self.parent_directory = parent_directory
        self.dependency_file_changed = False
        self._lines = []
        self._new_requirements = []

    def add(self, dependencies: list[str]):
        """add any number of dependencies to the end of list of dependencies."""
        for dep_str in dependencies:
            dep = Requirement(dep_str)
            if dep not in self.dependencies:
                self.dependencies.update({dep: None})
                self._new_requirements.append(str(dep))

    def write(self, dry_run: bool = False) -> Optional[ChangeSet]:
        """
        Write the updated dependency files if any changes were made.
        """
        if not (self.dependency_file and self._new_requirements):
            return None

        updated = self._lines + self._new_requirements + ["\n"]

        diff = "".join(difflib.unified_diff(self._lines, updated))
        # TODO: add a change entry for each new requirement
        # TODO: make sure to set the contextual_description=True in the properties bag

        if not dry_run:
            with open(self.dependency_file, "w", encoding="utf-8") as f:
                f.writelines(self._lines)
                f.writelines(self._new_requirements)

        self.dependency_file_changed = True
        return ChangeSet(str(self.dependency_file), diff, changes=[])

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
    def dependencies(self) -> dict[Requirement, None]:
        """
        Extract list of dependencies from requirements.txt file.
        Same order of requirements is maintained, no alphabetical sorting is done.
        """
        if not self.dependency_file:
            return {}

        with open(self.dependency_file, "r", encoding="utf-8") as f:
            self._lines = f.readlines()

        return {
            Requirement(line): None
            for x in self._lines
            # Skip empty lines and comments
            if (line := x.strip()) and not line.startswith("#")
        }
