from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from packaging.requirements import InvalidRequirement

from codemodder.dependency import Requirement


class FileType(Enum):
    REQ_TXT = "requirements.txt"
    TOML = "pyproject.toml"
    SETUP_PY = "setup.py"
    SETUP_CFG = "setup.cfg"


@dataclass(init=False)
class PackageStore:
    type: FileType
    file: Path
    dependencies: set[Requirement]
    py_versions: list[str]

    def __init__(
        self,
        type: FileType,
        file: Path,
        dependencies: set[str | Requirement],
        py_versions: list[str],
    ):
        self.type = type
        self.file = file
        self.dependencies = {
            x for x in {parse_requirement(dep) for dep in dependencies} if x
        }
        self.py_versions = py_versions

    def has_requirement(self, requirement: Requirement) -> bool:
        return requirement.name in {dep.name for dep in self.dependencies}


def parse_requirement(requirement: str | Requirement) -> Requirement:
    match requirement:
        case Requirement():
            return requirement
        case _:
            try:
                return Requirement(convert_py_version(requirement))
            except (InvalidRequirement, ValueError):
                return None


def convert_py_version(py_version: str) -> str:
    """
    Convert any dependency with ^ syntax to equivalent >=, < syntax.
    packaging.requirements does not support parsing dependencies with `^` syntax
    which is common in Poetry. For our internal representation we will convert it to

    `pandas^1.2.31` is equivalent to `pandas>=1.2.3,< 2.0.0`
    """
    if "^" in py_version:
        try:
            name, version = py_version.split("^")
            next_major_version = int(version.strip()[0]) + 1
            return f"{name}>={version},<{next_major_version}.0.0"
        except Exception:
            raise ValueError
    return py_version
