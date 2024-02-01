from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .utils.abc_dataclass import ABCDataclass


@dataclass
class LineInfo:
    line: int
    column: int
    snippet: str | None


@dataclass
class Location(ABCDataclass):
    file: Path
    start: LineInfo
    end: LineInfo


@dataclass
class Result(ABCDataclass):
    rule_id: str
    locations: list[Location]

    def match_location(self, pos, node):  # pylint: disable=unused-argument
        for location in self.locations:
            start_column = location.start.column
            end_column = location.end.column
            return (
                pos.start.line == location.start.line
                and (pos.start.column in (start_column - 1, start_column))
                and pos.end.line == location.end.line
                and (pos.end.column in (end_column - 1, end_column))
            )


class ResultSet(dict[str, dict[Path, list[Result]]]):
    def add_result(self, result: Result):
        for loc in result.locations:
            self.setdefault(result.rule_id, {}).setdefault(loc.file, []).append(result)

    def results_for_rule_and_file(self, rule_id: str, file: Path) -> list[Result]:
        return self.get(rule_id, {}).get(file, [])

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
