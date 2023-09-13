from pathlib import Path
from dataclasses import dataclass

from codemodder.change import Change


@dataclass
class ChangeSet:
    """A set of changes made to a file at `path`"""

    path: str
    diff: str
    changes: list[Change]

    def to_json(self):
        return {"path": self.path, "diff": self.diff, "changes": self.changes}


class CodemodExecutionContext:
    results_by_codemod: dict[str, list[ChangeSet]] = {}
    dependencies: set[str]
    directory: Path
    dry_run: bool = False

    def __init__(self, directory, dry_run):
        self.directory = directory
        self.dry_run = dry_run
        self.dependencies = set()
        self.results_by_codemod = {}

    def add_result(self, codemod_name, change_set):
        self.results_by_codemod.setdefault(codemod_name, []).append(change_set)

    def add_dependency(self, dependency: str):
        self.dependencies.add(dependency)
