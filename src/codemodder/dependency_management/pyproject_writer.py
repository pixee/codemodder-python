from typing import Optional

import tomlkit

from codemodder.dependency import Dependency
from codemodder.change import ChangeSet
from codemodder.dependency_management.base_dependency_writer import DependencyWriter


class PyprojectWriter(DependencyWriter):
    def write(
        self, dependencies: list[Dependency], dry_run: bool = False
    ) -> Optional[ChangeSet]:
        with open(self.path) as f:
            pyproject = tomlkit.load(f)
        # todo, convert dependencies to requirements
        pyproject["project"]["dependencies"].extend(map(str, dependencies))

        if not dry_run:
            with open(self.path, "w") as f:
                tomlkit.dump(pyproject, f)

        return None
