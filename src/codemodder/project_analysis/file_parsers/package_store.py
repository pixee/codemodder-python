from dataclasses import dataclass
from enum import Enum
from pathlib import Path

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
        type: FileType,  # pylint: disable=redefined-builtin
        file: Path,
        dependencies: set[str | Requirement],
        py_versions: list[str],
    ):
        self.type = type
        self.file = file
        self.dependencies = {
            dep if isinstance(dep, Requirement) else Requirement(dep)
            for dep in dependencies
        }
        self.py_versions = py_versions

    def has_requirement(self, requirement: Requirement) -> bool:
        return requirement.name in {dep.name for dep in self.dependencies}
