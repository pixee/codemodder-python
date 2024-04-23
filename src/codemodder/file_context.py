from dataclasses import dataclass, field
from pathlib import Path

from codemodder.codetf import Change, ChangeSet, UnfixedFinding
from codemodder.dependency import Dependency
from codemodder.result import Result
from codemodder.utils.timer import Timer


@dataclass
class FileContext:
    """
    Extra context for running codemods on a given file based on the cli parameters.
    """

    base_directory: Path
    file_path: Path
    line_exclude: list[int] = field(default_factory=list)
    line_include: list[int] = field(default_factory=list)
    results: list[Result] | None = field(default_factory=list)
    dependencies: set[Dependency] = field(default_factory=set)
    codemod_changes: list[Change] = field(default_factory=list)
    unfixed_findings: list[UnfixedFinding] = field(default_factory=list)
    changesets: list[ChangeSet] = field(default_factory=list)
    failures: list[Path] = field(default_factory=list)
    timer: Timer = field(default_factory=Timer)

    def add_dependency(self, dependency: Dependency):
        self.dependencies.add(dependency)

    def add_changeset(self, result: ChangeSet):
        self.changesets.append(result)

    def add_failure(self, filename: Path):
        self.failures.append(filename)
