from typing import Optional

from codemodder.codetf import ChangeSet
from codemodder.dependency import Dependency
from codemodder.dependency_management.base_dependency_writer import DependencyWriter
from codemodder.diff import create_diff


def original_lines_strategy(original_lines, i):
    return len(original_lines) + i + 1


class RequirementsTxtWriter(DependencyWriter):
    def add_to_file(
        self, dependencies: list[Dependency], dry_run: bool = False
    ) -> Optional[ChangeSet]:
        if (lines := self._parse_file()) is None:
            return None

        original_lines = lines.copy()
        if not original_lines[-1].endswith("\n"):
            original_lines[-1] += "\n"

        requirement_lines = []
        for dep in dependencies:
            requirement_lines.append(f"{dep.requirement}\n")

        updated_lines = original_lines + requirement_lines

        diff = create_diff(original_lines, updated_lines)

        if not dry_run:
            try:
                with open(self.path, "w", encoding="utf-8") as f:
                    f.writelines(updated_lines)
            except Exception:
                return None

        changes = self.build_changes(
            dependencies, original_lines_strategy, original_lines
        )
        return ChangeSet(
            path=str(self.path.relative_to(self.parent_directory)),
            diff=diff,
            changes=changes,
        )

    def _parse_file(self) -> Optional[list[str]]:
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return f.readlines()
        except Exception:
            return None
