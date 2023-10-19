from dataclasses import dataclass, field


@dataclass
class Change:
    lineNumber: str
    description: str
    properties: dict = field(default_factory=dict)
    packageActions: list = field(default_factory=list)

    def to_json(self):
        return {
            "lineNumber": self.lineNumber,
            "description": self.description,
            "properties": self.properties,
            "packageActions": self.packageActions,
        }


@dataclass
class ChangeSet:
    """A set of changes made to a file at `path`"""

    path: str
    diff: str
    changes: list[Change]

    def to_json(self):
        return {"path": self.path, "diff": self.diff, "changes": self.changes}
