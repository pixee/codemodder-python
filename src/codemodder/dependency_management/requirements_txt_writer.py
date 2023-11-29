from typing import Optional
from codemodder.dependency_management.base_dependency_writer import DependencyWriter
from codemodder.change import Action, Change, ChangeSet, PackageAction, Result
from codemodder.diff import create_diff
from codemodder.dependency import Dependency


class RequirementsTxtWriter(DependencyWriter):
    def add_to_file(
        self, dependencies: list[Dependency], dry_run: bool = False
    ) -> Optional[ChangeSet]:
        lines = self._parse_file()
        original_lines = lines.copy()
        if not original_lines[-1].endswith("\n"):
            original_lines[-1] += "\n"

        requirement_lines = [f"{dep.requirement}\n" for dep in dependencies]
        updated_lines = original_lines + requirement_lines

        diff = create_diff(original_lines, updated_lines)

        if not dry_run:
            with open(self.path, "w", encoding="utf-8") as f:
                f.writelines(updated_lines)

        changes = self.build_changes(dependencies, original_lines)
        return ChangeSet(
            str(self.path.relative_to(self.parent_directory)),
            diff,
            changes=changes,
        )

    def build_changes(
        self, dependencies: list[Dependency], original_lines: list[str]
    ) -> list[Change]:
        return [
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
            for i, dep in enumerate(dependencies)
        ]

    def _parse_file(self):
        with open(self.path, "r", encoding="utf-8") as f:
            return f.readlines()
