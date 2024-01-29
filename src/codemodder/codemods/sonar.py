from pathlib import Path
from codemodder.codemods.base_codemod import Metadata, Reference
from codemodder.codemods.base_detector import BaseDetector
from codemodder.codemods.base_transformer import BaseTransformerPipeline
from codemodder.context import CodemodExecutionContext
from codemodder.result import ResultSet
from codemodder.sonar_results import SonarResultSet
from core_codemods.api.core_codemod import CoreCodemod, SASTCodemod


class SonarCodemod(SASTCodemod):
    @property
    def origin(self):
        return "sonar"

    @classmethod
    def from_core_codemod(
        cls,
        name: str,
        other: CoreCodemod,
        rules: list[str],
        transformer: BaseTransformerPipeline | None = None,
        new_references: list[Reference] | None = None,
    ):  # pylint: disable=too-many-arguments
        return SonarCodemod(
            metadata=Metadata(
                name=name,
                summary="Sonar: " + other.summary,
                review_guidance=other._metadata.review_guidance,  # pylint: disable=protected-access
                references=(
                    other.references
                    if not new_references
                    else other.references + new_references
                ),
                description=f"This codemod acts upon the following Sonar rules: {str(rules)[1:-1]}.\n\n"
                + other.description,
            ),
            transformer=transformer if transformer else other.transformer,
            detector=SonarDetector(),
            requested_rules=rules,
        )


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
