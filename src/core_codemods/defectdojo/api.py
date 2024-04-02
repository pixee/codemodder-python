from pathlib import Path

from codemodder.codemods.base_detector import BaseDetector
from codemodder.context import CodemodExecutionContext
from codemodder.result import ResultSet
from core_codemods.api import SASTCodemod

from .results import DefectDojoResultSet


class DefectDojoDetector(BaseDetector):
    def apply(
        self,
        codemod_id: str,
        context: CodemodExecutionContext,
        files_to_analyze: list[Path],
    ) -> ResultSet:
        return DefectDojoResultSet()


class DefectDojoCodemod(SASTCodemod):
    @property
    def origin(self):
        return "defectdojo"
