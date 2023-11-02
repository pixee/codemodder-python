from dataclasses import dataclass
from pathlib import Path

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

    def match(self, pos):
        start_column = self.start.column
        end_column = self.end.column
        return (
            pos.start.line == self.start.line
            and (pos.start.column in (start_column - 1, start_column))
            and pos.end.line == self.end.line
            and (pos.end.column in (end_column - 1, end_column))
        )


@dataclass
class Result(ABCDataclass):
    rule_id: str
    locations: list[Location]


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
