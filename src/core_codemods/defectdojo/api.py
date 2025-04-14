from __future__ import annotations

from functools import cache
from typing import cast

from typing_extensions import override

from codemodder.codemods.api import Metadata, Reference, ToolMetadata, ToolRule
from codemodder.codemods.base_detector import BaseDetector
from codemodder.context import CodemodExecutionContext
from codemodder.llm import TokenUsage
from codemodder.result import ResultSet
from core_codemods.api import CoreCodemod, SASTCodemod

from .results import DefectDojoResultSet


class DefectDojoDetector(BaseDetector):
    def apply(
        self,
        codemod_id: str,
        context: CodemodExecutionContext,
    ) -> ResultSet:
        del codemod_id
        result_files = tuple(context.tool_result_files_map.get("defectdojo", ()))
        return _process_results(result_files)


@cache
def _process_results(result_files: tuple[str]) -> ResultSet:
    result_set = DefectDojoResultSet()
    for filename in result_files:
        result_set |= DefectDojoResultSet.from_json(filename)
    return result_set


class DefectDojoCodemod(SASTCodemod):
    @property
    def origin(self):
        return "defectdojo"

    @classmethod
    def from_core_codemod(
        cls,
        name: str,
        other: CoreCodemod,
        rule_id: str,
        rule_name: str,
        rule_url: str,
    ) -> DefectDojoCodemod:
        return DefectDojoCodemod(
            metadata=Metadata(
                name=name,
                summary=other.summary,
                review_guidance=other._metadata.review_guidance,
                references=(
                    other.references + [Reference(url=rule_url, description=rule_name)]
                ),
                description=other.description,
                tool=ToolMetadata(
                    name="DefectDojo",
                    rules=[
                        ToolRule(
                            id=rule_id,
                            name=rule_name,
                            url=rule_url,
                        )
                    ],
                ),
            ),
            transformer=other.transformer,
            detector=DefectDojoDetector(),
            requested_rules=[rule_id],
        )

    @override
    def apply(
        self,
        context: CodemodExecutionContext,
        remediation: bool = False,
    ) -> None | TokenUsage:
        if remediation:
            return self._apply_remediation(
                context,
                # We know this has a tool because we created it with `from_core_codemod`
                cast(ToolMetadata, self._metadata.tool).rule_ids,
            )
        return self._apply_hardening(
            context,
            # We know this has a tool because we created it with `from_core_codemod`
            cast(ToolMetadata, self._metadata.tool).rule_ids,
        )
