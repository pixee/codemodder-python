from typing import Optional
from codemodder.dependency_management.base_dependency_writer import DependencyWriter
from codemodder.change import Action, Change, ChangeSet, PackageAction, Result
from packaging.requirements import Requirement
from codemodder.diff import create_diff


class RequirementsTxtWriter(DependencyWriter):
    def write(
        self, dependencies: list[Requirement], dry_run: bool = False
    ) -> Optional[ChangeSet]:
        new_dependencies = self.add(dependencies)
        if new_dependencies:
            return self.add_to_file(new_dependencies, dry_run)
        return None

    def add_to_file(self, dependencies: list[Requirement], dry_run: bool):
        original_lines = self._parse_file()
        updated_lines = original_lines.copy()
        if not original_lines[-1].endswith("\n"):
            updated_lines[-1] += "\n"

        requirement_lines = [f"{dep.requirement}\n" for dep in dependencies]
        updated_lines += requirement_lines

        diff = create_diff(original_lines, updated_lines)

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
            for i, dep in enumerate(dependencies)
        ]

        if not dry_run:
            with open(self.path, "w", encoding="utf-8") as f:
                f.writelines(original_lines)
                f.writelines(requirement_lines)

        return ChangeSet(
            str(self.path.relative_to(self.parent_directory)),
            diff,
            changes=changes,
        )

    def _parse_file(self):
        with open(self.path, "r", encoding="utf-8") as f:
            return f.readlines()
