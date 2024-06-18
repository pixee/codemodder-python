from copy import deepcopy
from typing import Optional

import tomlkit

from codemodder.codetf import ChangeSet
from codemodder.dependency import Dependency
from codemodder.dependency_management.base_dependency_writer import DependencyWriter
from codemodder.diff import create_diff_and_linenums
from codemodder.logging import logger

TYPE_CHECKER_LIBRARIES = ["mypy", "pyright"]


def added_line_nums_strategy(lines, i):
    return lines[i]


class PyprojectWriter(DependencyWriter):
    def add_to_file(
        self, dependencies: list[Dependency], dry_run: bool = False
    ) -> Optional[ChangeSet]:
        pyproject = self._parse_file()
        original = deepcopy(pyproject)

        if pyproject.get("tool", {}).get("poetry", {}):
            # It's unlikely and bad practice to declare dependencies under [project].dependencies
            # and [tool.poetry.dependencies] but if it happens, we will give priority to poetry
            # and add dependencies under its system.
            self._update_poetry(pyproject, dependencies)
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

    def _update_poetry(
        self,
        pyproject: tomlkit.toml_document.TOMLDocument,
        dependencies: list[Dependency],
    ):
        add_newline = False

        if pyproject.get("tool", {}).get("poetry", {}).get("dependencies") is None:
            pyproject["tool"]["poetry"].update({"dependencies": {}})
            add_newline = True

        typing_location = find_typing_location(pyproject)

        for dep in dependencies:
            try:
                pyproject["tool"]["poetry"]["dependencies"].append(
                    dep.requirement.name, str(dep.requirement.specifier)
                )
            except tomlkit.exceptions.KeyAlreadyPresent:
                pass

            for type_stub_dependency in dep.type_stubs:
                if typing_location:
                    try:
                        keys = typing_location.split(".")
                        section = pyproject["tool"]["poetry"]
                        for key in keys:
                            section = section[key]
                        section.append(
                            type_stub_dependency.requirement.name,
                            str(type_stub_dependency.requirement.specifier),
                        )
                    except tomlkit.exceptions.KeyAlreadyPresent:
                        pass

        if add_newline:
            pyproject["tool"]["poetry"]["dependencies"].add(tomlkit.nl())


def find_typing_location(pyproject):
    """
    Look for a typing tool declared as a dependency in project.toml
    """
    locations = [
        "dependencies",
        "test.dependencies",
        "dev-dependencies",
        "dev.dependencies",
        "group.test.dependencies",
    ]
    poetry_section = pyproject.get("tool", {}).get("poetry", {})

    for location in locations:
        keys = location.split(".")
        section = poetry_section
        try:
            for key in keys:
                section = section[key]
            if any(checker in section for checker in TYPE_CHECKER_LIBRARIES):
                return location
        except KeyError:
            continue
    return None
