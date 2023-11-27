from dataclasses import dataclass
from packaging.requirements import Requirement


@dataclass
class PackageStore:
    type: str
    file: str
    dependencies: set[Requirement]
    py_versions: list[str]
