import configparser
import re
from typing import Optional

from codemodder.codetf import ChangeSet
from codemodder.dependency import Dependency
from codemodder.dependency_management.base_dependency_writer import DependencyWriter
from codemodder.diff import create_diff_and_linenums
from codemodder.logging import logger


def find_leading_whitespace(s):
    if match := re.match(r"(\s+)", s):
        return match.group(1)
    return ""  # pragma: no cover


def added_line_nums_strategy(lines, i):
    return lines[i]


class SetupCfgWriter(DependencyWriter):
    def add_to_file(
        self, dependencies: list[Dependency], dry_run: bool = False
    ) -> Optional[ChangeSet]:
        config = configparser.ConfigParser()

        try:
            config.read(self.path)
        except configparser.ParsingError:
            logger.debug("Unable to parse setup.cfg file.")
            return None

        if "options" not in config or not (
            defined_dependencies := config["options"].get("install_requires", "")
        ):
            logger.debug("Unable to add dependencies to setup.cfg file.")
            return None

        with open(self.path, "r", encoding="utf-8") as f:
            original_lines = f.readlines()

        if not (
            new_lines := self.build_new_lines(
                original_lines, defined_dependencies, dependencies
            )
        ):
            logger.debug("Unable to add dependencies to setup.cfg file.")
            return None

        if not dry_run:
            try:
                with open(self.path, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
            except Exception:
                logger.debug("Unable to add dependencies to setup.cfg file.")
                return None

        diff, added_line_nums = create_diff_and_linenums(original_lines, new_lines)

        changes = self.build_changes(
            dependencies, added_line_nums_strategy, added_line_nums
        )
        return ChangeSet(
            path=str(self.path.relative_to(self.parent_directory)),
            diff=diff,
            changes=changes,
        )

    def build_new_lines(
        self,
        original_lines: list[str],
        defined_dependencies: str,
        dependencies_to_add: list[Dependency],
    ) -> Optional[list[str]]:
        """
        configparser does not retain formatting or comment lines, so we have to build
        the output newline manually.
        """
        clean_lines = [s.strip() for s in original_lines]

        if newline_separated := len(defined_dependencies.split("\n")) > 1:
            last_dep_line = defined_dependencies.split("\n")[-1]
            dep_sep = "\n"
        else:
            # deps are in same line as install_requires key separated by commas
            last_dep_line = [
                line for line in clean_lines if line.endswith(defined_dependencies)
            ][-1]
            dep_sep = ","

        try:
            last_dep_idx = clean_lines.index(last_dep_line)
        except ValueError:
            # we were unable to find the last req line due to some formatting issue
            logger.debug("Unable to add dependencies to setup.cfg file.")
            return None

        if newline_separated:
            formatting = find_leading_whitespace(original_lines[last_dep_idx])
            new_deps = [
                f"{formatting}{dep.requirement}{dep_sep}" for dep in dependencies_to_add
            ]
            new_lines = (
                original_lines[: last_dep_idx + 1]
                + new_deps
                + original_lines[last_dep_idx + 1 :]
            )
        else:
            # new_deps added to existing deps line
            new_dep = ",".join(
                [f"{dep.requirement}{dep_sep}" for dep in dependencies_to_add]
            )
            new_dep_line = f"{original_lines[last_dep_idx].rstrip()}, {new_dep}\n"
            new_lines = (
                original_lines[:last_dep_idx]
                + [new_dep_line]
                + original_lines[last_dep_idx + 1 :]
            )

        return new_lines
