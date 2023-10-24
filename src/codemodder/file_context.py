from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from codemodder.change import Change
from codemodder.dependency import Dependency


@dataclass
class FileContext:
    """
    Extra context for running codemods on a given file based on the cli parameters.
    """

    file_path: Path
    line_exclude: List[int] = field(default_factory=list)
    line_include: List[int] = field(default_factory=list)
    results_by_id: Dict = field(default_factory=dict)
    dependencies: set[Dependency] = field(default_factory=set)
    codemod_changes: List[Change] = field(default_factory=list)

    def add_dependency(self, dependency: Dependency):
        self.dependencies.add(dependency)
