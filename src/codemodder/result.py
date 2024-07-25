from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Type

import libcst as cst
from libcst._position import CodeRange
from typing_extensions import Self

from codemodder.codetf import Finding

from .utils.abc_dataclass import ABCDataclass

if TYPE_CHECKING:
    from codemodder.context import CodemodExecutionContext


@dataclass
class LineInfo:
    line: int
    column: int = -1
    snippet: str | None = None


@dataclass
class Location(ABCDataclass):
    file: Path
    start: LineInfo
    end: LineInfo


class SarifLocation(Location):
    @classmethod
    @abstractmethod
    def from_sarif(cls, sarif_location) -> Self:
        pass


@dataclass
class LocationWithMessage:
    location: Location
    message: str


@dataclass(kw_only=True)
class Result(ABCDataclass):
    rule_id: str
    locations: list[Location]
    codeflows: list[list[Location]] = field(default_factory=list)
    related_locations: list[LocationWithMessage] = field(default_factory=list)
    finding: Finding | None = None

    def match_location(self, pos: CodeRange, node: cst.CSTNode) -> bool:
        del node
        return any(
            same_line(pos, location)
            and (
                pos.start.column
                in ((start_column := location.start.column) - 1, start_column)
            )
            and (
                pos.end.column in ((end_column := location.end.column) - 1, end_column)
            )
            for location in self.locations
        )


@dataclass(kw_only=True)
class SASTResult(Result):
    finding_id: str


@dataclass(kw_only=True)
class SarifResult(SASTResult, ABCDataclass):
    location_type: ClassVar[Type[SarifLocation]]

    @classmethod
    def from_sarif(
        cls, sarif_result, sarif_run, truncate_rule_id: bool = False
    ) -> Self:
        raise NotImplementedError

    @classmethod
    def extract_locations(cls, sarif_result) -> list[Location]:
        return [
            cls.location_type.from_sarif(location)
            for location in sarif_result["locations"]
        ]

    @classmethod
    def extract_related_locations(cls, sarif_result) -> list[LocationWithMessage]:
        return [
            LocationWithMessage(
                message=rel_location.get("message", {}).get("text", ""),
                location=cls.location_type.from_sarif(rel_location),
            )
            for rel_location in sarif_result.get("relatedLocations", [])
        ]

    @classmethod
    def extract_code_flows(cls, sarif_result) -> list[list[Location]]:
        return [
            [
                cls.location_type.from_sarif(locations.get("location"))
                for locations in threadflow.get("locations", {})
            ]
            for codeflow in sarif_result.get("codeFlows", {})
            for threadflow in codeflow.get("threadFlows", {})
        ]

    @classmethod
    def extract_rule_id(cls, result, sarif_run, truncate_rule_id: bool = False) -> str:
        if rule_id := result.get("ruleId"):
            return rule_id.split(".")[-1] if truncate_rule_id else rule_id

        # it may be contained in the 'rule' field through the tool component in the sarif file
        if "rule" in result:
            tool_index = result["rule"]["toolComponent"]["index"]
            rule_index = result["rule"]["index"]
            return sarif_run["tool"]["extensions"][tool_index]["rules"][rule_index][
                "id"
            ]

        raise ValueError("Could not extract rule id from sarif result.")


def same_line(pos: CodeRange, location: Location) -> bool:
    return pos.start.line == location.start.line and pos.end.line == location.end.line


def fuzzy_column_match(pos: CodeRange, location: Location) -> bool:
    """Checks that a result location is within the range of node's `pos` position"""
    return (
        pos.start.column <= location.start.column <= pos.end.column + 1
        and pos.start.column <= location.end.column <= pos.end.column + 1
    )


class ResultSet(dict[str, dict[Path, list[Result]]]):
    def add_result(self, result: Result):
        for loc in result.locations:
            self.setdefault(result.rule_id, {}).setdefault(loc.file, []).append(result)

    def results_for_rule_and_file(
        self, context: CodemodExecutionContext, rule_id: str, file: Path
    ) -> list[Result]:
        """
        Return list of results for a given rule and file.

        :param context: The codemod execution context
        :param rule_id: The rule ID
        :param file: The filename

        Some implementers may need to use the context to compute paths that are relative to the target directory.
        """
        return self.get(rule_id, {}).get(file.relative_to(context.directory), [])

    def files_for_rule(self, rule_id: str) -> list[Path]:
        return list(self.get(rule_id, {}).keys())

    def all_rule_ids(self) -> list[str]:
        return list(self.keys())

    def __or__(self, other):
        result = ResultSet(super().__or__(other))
        for k in self.keys() | other.keys():
            result[k] = list_dict_or(self[k], other[k])
        return result


def list_dict_or(
    dictionary: dict[Any, list[Any]], other: dict[Any, list[Any]]
) -> dict[Path, list[Any]]:
    result_dict = other | dictionary
    for k in other.keys() | dictionary.keys():
        result_dict[k] = dictionary[k] + other[k]
    return result_dict
