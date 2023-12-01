import tomlkit
from typing import Optional
from copy import deepcopy
from codemodder.dependency import Dependency
from codemodder.change import ChangeSet
from codemodder.dependency_management.base_dependency_writer import DependencyWriter
from codemodder.diff import create_diff_and_linenums
from codemodder.logging import logger


def added_line_nums_strategy(lines, i):
    return lines[i]


class PyprojectWriter(DependencyWriter):
    def add_to_file(
        self, dependencies: list[Dependency], dry_run: bool = False
    ) -> Optional[ChangeSet]:
        pyproject = self._parse_file()
        original = deepcopy(pyproject)

        try:
            pyproject["project"]["dependencies"].extend(
                [f"{dep.requirement}" for dep in dependencies]
            )
        except tomlkit.exceptions.NonExistentKey:
            logger.debug("Unable to add dependencies to pyproject.toml file.")
            return None

        diff, added_line_nums = create_diff_and_linenums(
            tomlkit.dumps(original).split("\n"), tomlkit.dumps(pyproject).split("\n")
        )

        if not dry_run:
            with open(self.path, "w", encoding="utf-8") as f:
                tomlkit.dump(pyproject, f)

        changes = self.build_changes(
            dependencies, added_line_nums_strategy, added_line_nums
        )
        return ChangeSet(
            str(self.path.relative_to(self.parent_directory)),
            diff,
            changes=changes,
        )

    def _parse_file(self):
        with open(self.path, encoding="utf-8") as f:
            return tomlkit.load(f)
