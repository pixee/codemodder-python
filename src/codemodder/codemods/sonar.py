from pathlib import Path
from codemodder.codemods.base_detector import BaseDetector
from codemodder.context import CodemodExecutionContext
from codemodder.result import ResultSet
from codemodder.sonar_results import SonarResultSet
from core_codemods.api.core_codemod import SASTCodemod


class SonarCodemod(SASTCodemod):
    @property
    def origin(self):
        return "sonar"


class SonarDetector(BaseDetector):
    _lazy_cache = None

    def _process_sonar_findings(self, sonar_json_files: list[str]) -> SonarResultSet:
        combined_result_set = SonarResultSet()
        for file in sonar_json_files or []:
            combined_result_set |= SonarResultSet.from_json(file)
        return combined_result_set

    def apply(
        self,
        codemod_id: str,
        context: CodemodExecutionContext,
        files_to_analyze: list[Path],
    ) -> ResultSet:
        if not self._lazy_cache:
            self._lazy_cache = self._process_sonar_findings(
                context.tool_result_files_map.get("sonar", [])
            )
        return self._lazy_cache
