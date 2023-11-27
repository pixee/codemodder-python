import tomlkit
from typing import Optional
from copy import deepcopy
from codemodder.dependency import Dependency
from codemodder.change import Action, Change, ChangeSet, PackageAction, Result
from codemodder.dependency_management.base_dependency_writer import DependencyWriter
from codemodder.diff import create_diff


class PyprojectWriter(DependencyWriter):
    def add_to_file(
        self, dependencies: list[Dependency], dry_run: bool = False
    ) -> Optional[ChangeSet]:
        pyproject = self._parse_file()
        original = deepcopy(pyproject)
        pyproject["project"]["dependencies"].extend(
            [f"{dep.requirement}" for dep in dependencies]
        )

        diff = create_diff(
            tomlkit.dumps(original).split("\n"), tomlkit.dumps(pyproject).split("\n")
        )

        added_lines = self.calc_new_line_nums(original, pyproject)

        if not dry_run:
            with open(self.path, "w") as f:
                tomlkit.dump(pyproject, f)

        # TODO: compute the correct line num, maybe use the diff?
        last_dep_line = ""
        changes = [
            Change(
                lineNumber=added_lines[i],
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

    def calc_new_line_nums(self, original, updated):
        added_lines = []
        current_line_number = 0
        import difflib

        diff_lines = list(
            difflib.unified_diff(
                tomlkit.dumps(original).split("\n"),
                tomlkit.dumps(updated).split("\n"),
                lineterm="",
            )
        )
        for line in diff_lines:
            if line.startswith("@@"):
                # Extract the starting line number for the updated file from the diff metadata.
                # The format is @@ -x,y +a,b @@, where a is the starting line number in the updated file.
                start_line = line.split(" ")[2]
                current_line_number = (
                    int(start_line.split(",")[0][1:]) - 1
                )  # Subtract 1 because line numbers are 1-indexed

            elif line.startswith("+"):
                # Increment line number for each line in the updated file
                current_line_number += 1
                if not line.startswith("++"):  # Ignore the diff metadata lines
                    added_lines.append(current_line_number)

            elif not line.startswith("-"):
                # Increment line number for unchanged/context lines
                current_line_number += 1

        return added_lines
