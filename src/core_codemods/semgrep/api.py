from codemodder.codemods.base_codemod import Metadata, Reference, ToolMetadata, ToolRule
from codemodder.codemods.base_transformer import BaseTransformerPipeline
from codemodder.codemods.semgrep import SemgrepSarifFileDetector
from core_codemods.api.core_codemod import CoreCodemod, SASTCodemod


def semgrep_url_from_id(rule_id: str) -> str:
    return f"https://semgrep.dev/r?q={rule_id}"


class SemgrepCodemod(SASTCodemod):
    @property
    def origin(self):
        return "semgrep"

    @classmethod
    def from_core_codemod(
        cls,
        name: str,
        other: CoreCodemod,
        rules: list[ToolRule],
        transformer: BaseTransformerPipeline | None = None,
    ):
        return SemgrepCodemod(
            metadata=Metadata(
                name=name,
                summary=other.summary,
                review_guidance=other._metadata.review_guidance,
                references=(
                    other.references
                    + [
                        Reference(
                            url=semgrep_url_from_id(rule.id), description=rule.name
                        )
                        for rule in rules
                    ]
                ),
                description=other.description,
                tool=ToolMetadata(
                    name="Semgrep",
                    rules=rules,
                ),
            ),
            transformer=transformer if transformer else other.transformer,
            detector=SemgrepSarifFileDetector(),
            requested_rules=[rule.id for rule in rules],
        )
