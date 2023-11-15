from typing import Optional

import tomlkit

from codemodder.dependency import Requirement
from codemodder.dependency_writer import DependencyWriter, ChangeSet


class PyprojectWriter(DependencyWriter):
    def write(
        self, dependencies: list[Requirement], dry_run: bool = False
    ) -> Optional[ChangeSet]:
        with open(self.path) as f:
            pyproject = tomlkit.load(f)

        pyproject["project"]["dependencies"].extend(map(str, dependencies))

        if not dry_run:
            with open(self.path, "w") as f:
                tomlkit.dump(pyproject, f)

        return None
