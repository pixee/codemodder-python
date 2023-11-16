from pathlib import Path

import tomlkit

from codemodder.dependency import Requirement


def update_pyproject_dependencies(
    pyproject_path: str | Path,
    dependencies: list[Requirement],
    dry_run: bool = False,
):
    with open(pyproject_path) as f:
        pyproject = tomlkit.load(f)

    pyproject["project"]["dependencies"].extend(map(str, dependencies))

    if not dry_run:
        with open(pyproject_path, "w") as f:
            tomlkit.dump(pyproject, f)
