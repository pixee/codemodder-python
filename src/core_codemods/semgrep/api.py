from functools import cache
from pathlib import Path

from codemodder.codemods.base_codemod import Metadata, Reference, ToolMetadata, ToolRule
from codemodder.codemods.base_detector import BaseDetector
from codemodder.codemods.base_transformer import BaseTransformerPipeline
from codemodder.context import CodemodExecutionContext
from codemodder.result import ResultSet
from codemodder.semgrep import SemgrepResultSet
from core_codemods.api.core_codemod import CoreCodemod, SASTCodemod


class SemgrepCodemod(SASTCodemod):
    @property
    def origin(self):
        return "semgrep"

    @classmethod
    def from_core_codemod(
        cls,
        name: str,
        other: CoreCodemod,
        rule_id: str,
        rule_name: str,
        transformer: BaseTransformerPipeline | None = None,
    ):
        rule_url = f"https://semgrep.dev/r?q={rule_id}"
        return SemgrepCodemod(
            metadata=Metadata(
                name=name,
                summary=other.summary,
                review_guidance=other._metadata.review_guidance,
                references=(
                    other.references + [Reference(url=rule_url, description=rule_name)]
                ),
                description=other.description,
                tool=ToolMetadata(
                    name="Semgrep",
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
            detector=SemgrepSarifFileDetector(),
            requested_rules=[rule_id],
        )


class SemgrepSarifFileDetector(BaseDetector):
    def apply(
        self,
        codemod_id: str,
        context: CodemodExecutionContext,
        files_to_analyze: list[Path],
    ) -> ResultSet:
        del codemod_id
        del files_to_analyze
        return process_semgrep_findings(
            tuple(context.tool_result_files_map.get("semgrep", ()))
        )  # Convert list to tuple for cache hashability


@cache
def process_semgrep_findings(semgrep_sarif_files: tuple[str]) -> ResultSet:
    results = SemgrepResultSet()
    for file in semgrep_sarif_files or ():
        results |= SemgrepResultSet.from_sarif(file)
    return results
