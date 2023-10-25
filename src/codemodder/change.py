from dataclasses import dataclass, field
from enum import Enum


class Action(Enum):
    ADD = "add"
    REMOVE = "remove"


class Result(Enum):
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PackageAction:
    action: Action
    result: Result
    package: str

    def to_json(self):
        return {
            "action": self.action.value.upper(),
            "result": self.result.value.upper(),
            "package": self.package,
        }


@dataclass
class Change:
    lineNumber: int
    description: str
    properties: dict = field(default_factory=dict)
    packageActions: list[PackageAction] = field(default_factory=list)

    def to_json(self):
        return {
            # Not sure why this is a string but it's in the spec
            "lineNumber": str(self.lineNumber),
            "description": self.description,
            "properties": self.properties,
            "packageActions": [pa.to_json() for pa in self.packageActions],
        }


@dataclass
class ChangeSet:
    """A set of changes made to a file at `path`"""

    path: str
    diff: str
    changes: list[Change]

    def to_json(self):
        return {
            "path": self.path,
            "diff": self.diff,
            "changes": [x.to_json() for x in self.changes],
        }
