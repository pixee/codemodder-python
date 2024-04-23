import json
from functools import cache
from pathlib import Path

import libcst as cst
from libcst._position import CodeRange
from typing_extensions import Self, override

from codemodder.codetf import Finding, Rule
from codemodder.result import LineInfo, Location, ResultSet, SASTResult


class DefectDojoLocation(Location):
    @classmethod
    def from_finding(cls, finding: dict) -> Self:
        return cls(
            file=Path(finding["file_path"]),
            # TODO: parse snippet from "description" field?
            start=LineInfo(finding["line"]),
            end=LineInfo(finding["line"]),
        )


class DefectDojoResult(SASTResult):
    @classmethod
    def from_finding(cls, finding: dict) -> Self:
        return cls(
            finding_id=finding["id"],
            rule_id=finding["title"],
            locations=[DefectDojoLocation.from_finding(finding)],
            finding=Finding(
                id=str(finding["id"]),
                rule=Rule(
                    # TODO: it's possible that these fields actually come from the codemod and not the result
                    id=str(finding["title"]),
                    name=str(finding["title"]),
                    url=None,
                ),
            ),
        )

    @override
    def match_location(self, pos: CodeRange, node: cst.CSTNode) -> bool:
        """
        Match location for DefectDojo results

        Since DefectDojo does not provide column information, we can only match based on line number.
        We check whether the start line of the result is within the range of the node.
        """
        del node
        return any(
            pos.start.line <= location.start.line <= pos.end.line
            for location in self.locations
        )


class DefectDojoResultSet(ResultSet):
    @classmethod
    @cache
    def from_json(cls, json_file: str | Path) -> Self:
        with open(json_file, "r", encoding="utf-8") as file:
            data = json.load(file)

        result_set = cls()
        for finding in data.get("results"):
            result_set.add_result(DefectDojoResult.from_finding(finding))

        return result_set
