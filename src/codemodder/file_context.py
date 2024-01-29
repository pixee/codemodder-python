from dataclasses import dataclass, field
from pathlib import Path

from codemodder.change import Change, ChangeSet
from codemodder.dependency import Dependency
from codemodder.result import Result
from codemodder.utils.timer import Timer


@dataclass
class FileContext:  # pylint: disable=too-many-instance-attributes
    """
    Extra context for running codemods on a given file based on the cli parameters.
    """

    base_directory: Path
    file_path: Path
    line_exclude: list[int] = field(default_factory=list)
    line_include: list[int] = field(default_factory=list)
    findings: list[Result] | None = field(default_factory=list)
    dependencies: set[Dependency] = field(default_factory=set)
    codemod_changes: list[Change] = field(default_factory=list)
    results: list[ChangeSet] = field(default_factory=list)
    failures: list[Path] = field(default_factory=list)
    timer: Timer = field(default_factory=Timer)

    def add_dependency(self, dependency: Dependency):
        self.dependencies.add(dependency)

    def add_result(self, result: ChangeSet):
        self.results.append(result)

    def add_failure(self, filename: Path):
        self.failures.append(filename)
