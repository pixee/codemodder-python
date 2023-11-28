import tomlkit
from typing import Optional
from copy import deepcopy
from codemodder.dependency import Dependency
from codemodder.change import Action, Change, ChangeSet, PackageAction, Result
from codemodder.dependency_management.base_dependency_writer import DependencyWriter
from codemodder.diff import create_diff_and_linenums


class PyprojectWriter(DependencyWriter):
    def add_to_file(
        self, dependencies: list[Dependency], dry_run: bool = False
    ) -> Optional[ChangeSet]:
        pyproject = self._parse_file()
        original = deepcopy(pyproject)
        pyproject["project"]["dependencies"].extend(
            [f"{dep.requirement}" for dep in dependencies]
        )

        diff, added_line_nums = create_diff_and_linenums(
            tomlkit.dumps(original).split("\n"), tomlkit.dumps(pyproject).split("\n")
        )

        if not dry_run:
            with open(self.path, "w") as f:
                tomlkit.dump(pyproject, f)

        changes = [
            Change(
                lineNumber=added_line_nums[i],
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
        return ChangeSet(
            str(self.path.relative_to(self.parent_directory)),
            diff,
            changes=changes,
        )

    def _parse_file(self):
        with open(self.path) as f:
            return tomlkit.load(f)
