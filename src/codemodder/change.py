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
