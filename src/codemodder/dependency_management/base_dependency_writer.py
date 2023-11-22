from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import Optional

from codemodder.change import ChangeSet
from codemodder.dependency import Requirement


class DependencyWriter(metaclass=ABCMeta):
    path: Path

    def __init__(self, path: str | Path):
        self.path = Path(path)

    @abstractmethod
    def write(
        self, dependencies: list[Requirement], dry_run: bool = False
    ) -> Optional[ChangeSet]:
        pass
