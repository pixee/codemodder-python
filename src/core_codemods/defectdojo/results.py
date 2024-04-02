import json
from functools import cache
from pathlib import Path

from typing_extensions import Self

from codemodder.result import LineInfo, Location, Result, ResultSet


class DefectDojoLocation(Location):
    @classmethod
    def from_finding(cls, finding: dict) -> Self:
        return cls(
            file=Path(finding["file_path"]),
            # TODO: parse snippet from "description" field?
            start=LineInfo(finding["line"]),
            end=LineInfo(finding["line"]),
        )


class DefectDojoResult(Result):
    @classmethod
    def from_finding(cls, finding: dict) -> Self:
        return cls(
            rule_id=finding["title"],
            locations=[DefectDojoLocation.from_finding(finding)],
        )


class DefectDojoResultSet(ResultSet):
    @cache
    @classmethod
    def from_json(cls, json_file: str | Path) -> Self:
        with open(json_file, "r", encoding="utf-8") as file:
            data = json.load(file)

        result_set = cls()
        for finding in data.get("results"):
            result_set.add_result(DefectDojoResult.from_finding(finding))

        return result_set
