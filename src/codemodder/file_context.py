from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from codemodder.change import Change, ChangeSet
from codemodder.dependency import Dependency


@dataclass
class FileContext:  # pylint: disable=too-many-instance-attributes
    """
    Extra context for running codemods on a given file based on the cli parameters.
    """

    base_directory: Path
    file_path: Path
    line_exclude: List[int] = field(default_factory=list)
    line_include: List[int] = field(default_factory=list)
    results_by_id: Dict = field(default_factory=dict)
    dependencies: set[Dependency] = field(default_factory=set)
    codemod_changes: List[Change] = field(default_factory=list)
    results: List[ChangeSet] = field(default_factory=list)
    failures: List[Path] = field(default_factory=list)

    def add_dependency(self, dependency: Dependency):
        self.dependencies.add(dependency)

    def add_result(self, result: ChangeSet):
        self.results.append(result)

    def add_failure(self, filename: Path):
        self.failures.append(filename)
