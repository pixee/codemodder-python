from codemodder.codemods.api import SimpleCodemod
from codemodder.codemods.base_codemod import Metadata, Reference, ToolMetadata, ToolRule
from codemodder.codemods.base_transformer import BaseTransformerPipeline
from codemodder.codemods.libcst_transformer import LibcstTransformerPipeline
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
        rule_id: str,
        rule_name: str,
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
                            url=semgrep_url_from_id(rule_id), description=rule_name
                        )
                    ]
                ),
                description=other.description,
                tool=ToolMetadata(
                    name="Semgrep",
                    rules=[
                        ToolRule(
                            id=rule_id,
                            name=rule_name,
                            url=semgrep_url_from_id(rule_id),
                        )
                    ],
                ),
            ),
            transformer=transformer if transformer else other.transformer,
            detector=SemgrepSarifFileDetector(),
            requested_rules=[rule_id],
        )

    @classmethod
    def from_import_modifier_codemod(
        cls,
        name: str,
        other: type[SimpleCodemod],
        rule_id: str,
        rule_name: str,
    ):
        metadata = other.metadata
        return SemgrepCodemod(
            metadata=Metadata(
                name=name,
                summary=metadata.summary,
                review_guidance=metadata.review_guidance,
                references=(
                    metadata.references
                    + [
                        Reference(
                            url=semgrep_url_from_id(rule_id), description=rule_name
                        )
                    ]
                ),
                description=other.change_description,
                tool=ToolMetadata(
                    name="Semgrep",
                    rules=[
                        ToolRule(
                            id=rule_id,
                            name=rule_name,
                            url=semgrep_url_from_id(rule_id),
                        )
                    ],
                ),
            ),
            transformer=LibcstTransformerPipeline(other),
            detector=SemgrepSarifFileDetector(),
            requested_rules=[rule_id],
        )
