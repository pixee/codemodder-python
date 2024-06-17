from copy import deepcopy
from typing import Optional

import tomlkit

from codemodder.codetf import ChangeSet
from codemodder.dependency import Dependency
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

        if poetry_data := pyproject.get("tool", {}).get("poetry", {}):
            add_newline = False
            # It's unlikely and bad practice to declare dependencies under [project].dependencies
            # and [tool.poetry.dependencies] but if it happens, we will give priority to poetry
            # and add dependencies under its system.
            if poetry_data.get("dependencies") is None:
                pyproject["tool"]["poetry"].append("dependencies", {})
                add_newline = True

            for dep in dependencies:
                try:
                    pyproject["tool"]["poetry"]["dependencies"].append(
                        dep.requirement.name, str(dep.requirement.specifier)
                    )
                except tomlkit.exceptions.KeyAlreadyPresent:
                    pass

            if add_newline:
                pyproject["tool"]["poetry"]["dependencies"].add(tomlkit.nl())

        else:
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
            path=str(self.path.relative_to(self.parent_directory)),
            diff=diff,
            changes=changes,
        )

    def _parse_file(self):
        with open(self.path, encoding="utf-8") as f:
            return tomlkit.load(f)
