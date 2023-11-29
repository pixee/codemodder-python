from dataclasses import dataclass
from enum import Enum
from packaging.requirements import Requirement


class FileType(Enum):
    REQ_TXT = "requirements.txt"
    TOML = "pyproject.toml"
    SETUP_PY = "setup.py"
    SETUP_CFG = "setup.cfg"


@dataclass
class PackageStore:
    type: FileType
    file: str
    dependencies: set[Requirement]
    py_versions: list[str]
