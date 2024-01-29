from abc import ABCMeta, abstractmethod
from pathlib import Path

from codemodder.context import CodemodExecutionContext
from codemodder.result import ResultSet


class BaseDetector(metaclass=ABCMeta):
    @abstractmethod
    def apply(
        self,
        codemod_id: str,
        context: CodemodExecutionContext,
        files_to_analyze: list[Path],
    ) -> ResultSet: ...
