from functools import cache
from pathlib import Path

from codemodder.codemods.base_codemod import Metadata, Reference, ToolMetadata, ToolRule
from codemodder.codemods.base_detector import BaseDetector
from codemodder.codemods.base_transformer import BaseTransformerPipeline
from codemodder.context import CodemodExecutionContext
from codemodder.result import ResultSet
from core_codemods.api.core_codemod import CoreCodemod, SASTCodemod
from core_codemods.sonar.results import SonarResultSet, sonar_url_from_id


class SonarCodemod(SASTCodemod):
    @property
    def origin(self):
        return "sonar"

    @classmethod
    def from_core_codemod(
        cls,
        name: str,
        other: CoreCodemod,
        rule_id: str,
        rule_name: str,
        transformer: BaseTransformerPipeline | None = None,
    ):
        rule_url = sonar_url_from_id(rule_id)
        return SonarCodemod(
            metadata=Metadata(
                name=name,
                summary=other.summary,
                review_guidance=other._metadata.review_guidance,
                references=(
                    other.references + [Reference(url=rule_url, description=rule_name)]
                ),
                description=other.description,
                tool=ToolMetadata(
                    name="Sonar",
                    rules=[
                        ToolRule(
                            id=rule_id,
                            name=rule_name,
                            url=rule_url,
                        )
                    ],
                ),
            ),
            transformer=transformer if transformer else other.transformer,
            detector=SonarDetector(),
            requested_rules=[rule_id],
        )


class SonarDetector(BaseDetector):
    def apply(
        self,
        codemod_id: str,
        context: CodemodExecutionContext,
        files_to_analyze: list[Path],
    ) -> ResultSet:
        del codemod_id
        del files_to_analyze
        sonar_findings = process_sonar_findings(
            tuple(
                context.tool_result_files_map.get("sonar", ())
            )  # Convert list to tuple for cache hashability
        )
        return sonar_findings


@cache
def process_sonar_findings(sonar_json_files: tuple[str]) -> SonarResultSet:
    combined_result_set = SonarResultSet()
    for file in sonar_json_files or ():
        combined_result_set |= SonarResultSet.from_json(file)
    return combined_result_set
