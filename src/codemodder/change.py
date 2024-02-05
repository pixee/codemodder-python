from dataclasses import dataclass, field
from enum import Enum


class Action(Enum):
    ADD = "add"
    REMOVE = "remove"


class Result(Enum):
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class DiffSide(Enum):
    LEFT = "left"
    RIGHT = "right"


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
    # All of our changes are currently treated as additive, so it makes sense
    # for the comments to appear on the RIGHT side of the split diff. Eventually we
    # may want to differentiate between LEFT and RIGHT, but for now we'll just
    # default to RIGHT.
    diffSide: DiffSide = field(default=DiffSide.RIGHT)
    properties: dict = field(default_factory=dict)
    packageActions: list[PackageAction] = field(default_factory=list)

    def to_json(self):
        return {
            # Not sure why this is a string but it's in the spec
            "lineNumber": str(self.lineNumber),
            "description": self.description,
            "properties": self.properties,
            "diffSide": self.diffSide.value.lower(),
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
