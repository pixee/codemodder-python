from dataclasses import dataclass
from packaging.requirements import Requirement


@dataclass
class PackageStore:
    type: str
    file: str
    dependencies: list[Requirement]
    py_versions: list[str]
