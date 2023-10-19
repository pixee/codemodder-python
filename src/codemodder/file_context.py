from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


@dataclass
class FileContext:
    """
    Extra context for running codemods on a given file based on the cli parameters.
    """

    file_path: Path
    line_exclude: List[int]
    line_include: List[int]
    results_by_id: Dict
    dependencies: set[str] = field(default_factory=set)

    def __post_init__(self):
        if self.line_include is None:
            self.line_include = []
        if self.line_exclude is None:
            self.line_exclude = []
        self.codemod_changes = []

    def add_dependency(self, dependency: str):
        self.dependencies.add(dependency)
