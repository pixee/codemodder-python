from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import libcst as cst
from libcst._position import CodeRange

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


@dataclass
class Result(ABCDataclass):
    rule_id: str
    locations: list[Location]

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
