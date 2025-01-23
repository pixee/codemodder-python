from functools import cache

from codemodder.codemods.base_codemod import Metadata, Reference, ToolMetadata, ToolRule
from codemodder.codemods.base_detector import BaseDetector
from codemodder.codemods.base_transformer import BaseTransformerPipeline
from codemodder.context import CodemodExecutionContext
from codemodder.result import ResultSet
from core_codemods.api.core_codemod import CoreCodemod, SASTCodemod
from core_codemods.sonar.results import SonarResultSet, sonar_url_from_id


class SonarCodemod(SASTCodemod):

    def __init__(
        self,
        *,
        metadata: Metadata,
        transformer: BaseTransformerPipeline,
        default_extensions: list[str] | None = None,
        requested_rules: list[str] | None = None,
        provider: str | None = None,
    ):
        super().__init__(
            metadata=metadata,
            detector=SonarDetector(),
            transformer=transformer,
            default_extensions=default_extensions,
            requested_rules=requested_rules,
            provider=provider,
        )

    @property
    def origin(self):
        return "sonar"

    @classmethod
    def from_core_codemod_with_multiple_rules(
        cls,
        name: str,
        other: CoreCodemod,
        rules: list[ToolRule],
        transformer: BaseTransformerPipeline | None = None,
    ):
        return SonarCodemod(
            metadata=Metadata(
                name=name,
                summary=other.summary,
                review_guidance=other._metadata.review_guidance,
                references=(
                    other.references
                    + [Reference(url=tr.url or "", description=tr.name) for tr in rules]
                ),
                description=other.description,
                tool=ToolMetadata(
                    name="Sonar",
                    rules=rules,
                ),
            ),
            transformer=transformer if transformer else other.transformer,
            default_extensions=other.default_extensions,
            requested_rules=[tr.id for tr in rules],
        )

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
        rules = [
            ToolRule(
                id=rule_id,
                name=rule_name,
                url=rule_url,
            ),
        ]
        return cls.from_core_codemod_with_multiple_rules(
            name, other, rules, transformer
        )


class SonarDetector(BaseDetector):
    def apply(
        self,
        codemod_id: str,
        context: CodemodExecutionContext,
    ) -> ResultSet:
        del codemod_id
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
