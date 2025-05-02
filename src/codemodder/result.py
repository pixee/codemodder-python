from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Sequence, Type, TypeVar

import libcst as cst
from boltons.setutils import IndexedSet
from libcst._position import CodeRange
from sarif_pydantic import Location as LocationModel
from sarif_pydantic import Result as ResultModel
from sarif_pydantic import Run
from typing_extensions import Self

from codemodder.codetf import Finding, Rule

from .utils.abc_dataclass import ABCDataclass

if TYPE_CHECKING:
    from codemodder.context import CodemodExecutionContext


@dataclass(frozen=True)
class LineInfo:
    line: int
    column: int = -1
    snippet: str | None = None


@dataclass(frozen=True)
class Location(ABCDataclass):
    file: Path
    start: LineInfo
    end: LineInfo


@dataclass(frozen=True)
class SarifLocation(Location):
    @staticmethod
    def get_snippet(sarif_location: LocationModel) -> str | None:
        return sarif_location.message.text if sarif_location.message else None

    @staticmethod
    def process_uri(run: Run, sarif_location: LocationModel, uri: str) -> Path:
        del sarif_location
        return Path(uri)

    @classmethod
    def from_sarif(cls, run: Run, sarif_location: LocationModel) -> Self:
        if not (physical_location := sarif_location.physical_location):
            raise ValueError("Sarif location does not have a physical location")
        if not (artifact_location := physical_location.artifact_location):
            raise ValueError("Sarif location does not have an artifact location")
        if not (region := physical_location.region):
            raise ValueError("Sarif location does not have a region")
        if not (uri := artifact_location.uri):
            raise ValueError("Sarif location does not have a uri")

        file = cls.process_uri(run, sarif_location, uri)
        snippet = cls.get_snippet(sarif_location)
        start = LineInfo(
            line=region.start_line or -1,
            column=region.start_column or -1,
            snippet=snippet,
        )
        end = LineInfo(
            line=region.end_line or -1,
            column=region.end_column or -1,
            snippet=snippet,
        )
        return cls(file=file, start=start, end=end)


@dataclass(frozen=True)
class LocationWithMessage:
    location: Location
    message: str


@dataclass(frozen=True, kw_only=True)
class Result(ABCDataclass):
    rule_id: str
    locations: Sequence[Location]
    codeflows: Sequence[Sequence[Location]] = field(default_factory=tuple)
    related_locations: Sequence[LocationWithMessage] = field(default_factory=tuple)
    finding: Finding

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

    def __hash__(self):
        return hash(self.rule_id)

    def get_locations(self) -> Sequence[Sequence[Location]]:
        return self.codeflows or (
            [self.locations]
            if self.locations
            else [[loc.location for loc in self.related_locations]]
        )


@dataclass(frozen=True, kw_only=True)
class SASTResult(Result):
    finding_id: str


@dataclass(frozen=True, kw_only=True)
class SarifResult(SASTResult):
    finding_msg: str | None = None
    location_type: ClassVar[Type[SarifLocation]]

    @classmethod
    def from_sarif(
        cls, sarif_result: ResultModel, sarif_run: Run, truncate_rule_id: bool = False
    ) -> Self:
        rule_id = cls.extract_rule_id(sarif_result, sarif_run, truncate_rule_id)
        finding_id = cls.extract_finding_id(sarif_result)
        if not finding_id:
            raise ValueError("Result does not have a finding_id.")
        return cls(
            rule_id=rule_id,
            locations=cls.extract_locations(sarif_result, sarif_run),
            codeflows=cls.extract_code_flows(sarif_result, sarif_run),
            related_locations=cls.extract_related_locations(sarif_result, sarif_run),
            finding_id=finding_id,
            finding=Finding(
                id=finding_id,
                rule=Rule(
                    id=rule_id,
                    name=cls.extract_finding_rule_name(sarif_result, sarif_run),
                    url=cls.rule_url_from_id(sarif_result, sarif_run, rule_id),
                ),
            ),
            finding_msg=cls.extract_finding_message(sarif_result, sarif_run),
        )

    @classmethod
    def extract_finding_rule_name(
        cls, sarif_result: ResultModel, sarif_run: Run
    ) -> str:
        return cls.extract_rule_id(sarif_result, sarif_run)

    @classmethod
    def extract_finding_message(
        cls, sarif_result: ResultModel, sarif_run: Run
    ) -> str | None:
        del sarif_run
        return sarif_result.message.text

    @classmethod
    def rule_url_from_id(
        cls, result: ResultModel, run: Run, rule_id: str
    ) -> str | None:
        del result, run, rule_id
        return None

    @classmethod
    def extract_locations(
        cls, sarif_result: ResultModel, run: Run
    ) -> Sequence[Location]:
        return tuple(
            [
                cls.location_type.from_sarif(run, location)
                for location in sarif_result.locations or []
            ]
        )

    @classmethod
    def extract_related_locations(
        cls, sarif_result: ResultModel, run: Run
    ) -> Sequence[LocationWithMessage]:
        return tuple(
            [
                LocationWithMessage(
                    message=rel_location.message.text,
                    location=cls.location_type.from_sarif(run, rel_location),
                )
                for rel_location in sarif_result.related_locations or []
                if rel_location.message
            ]
        )

    @classmethod
    def extract_code_flows(
        cls, sarif_result: ResultModel, run: Run
    ) -> Sequence[Sequence[Location]]:
        return tuple(
            [
                tuple(
                    [
                        cls.location_type.from_sarif(run, locations.location)
                        for locations in threadflow.locations or []
                        if locations.location
                    ]
                )
                for codeflow in sarif_result.code_flows or []
                for threadflow in codeflow.thread_flows or []
            ]
        )

    @classmethod
    def extract_rule_id(
        cls, result: ResultModel, sarif_run: Run, truncate_rule_id: bool = False
    ) -> str:
        if rule_id := result.rule_id:
            return rule_id.split(".")[-1] if truncate_rule_id else rule_id

        # it may be contained in the 'rule' field through the tool component in the sarif file
        if (
            (rule := result.rule)
            and sarif_run.tool.extensions
            and rule.tool_component
            and rule.tool_component.index is not None
        ):
            tool_index = rule.tool_component.index
            rule_index = rule.index
            return sarif_run.tool.extensions[tool_index].rules[rule_index].id

        raise ValueError("Could not extract rule id from sarif result.")

    @classmethod
    def extract_finding_id(cls, result: ResultModel) -> str | None:
        return str(result.guid or "") or str(result.correlation_guid or "") or None


def same_line(pos: CodeRange, location: Location) -> bool:
    return pos.start.line == location.start.line and pos.end.line == location.end.line


def fuzzy_column_match(pos: CodeRange, location: Location) -> bool:
    """Checks that a result location is within the range of node's `pos` position"""
    return (
        pos.start.column <= location.start.column <= pos.end.column + 1
        and pos.start.column <= location.end.column <= pos.end.column + 1
    )


ResultType = TypeVar("ResultType", bound=Result)


class ResultSet(dict[str, dict[Path, list[ResultType]]]):
    results_for_rule: dict[str, list[ResultType]]
    # stores SARIF runs.tool data
    tools: list[dict[str, dict]]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.results_for_rule = {}
        self.tools = []

    def add_result(self, result: ResultType):
        self.results_for_rule.setdefault(result.rule_id, []).append(result)
        for loc in result.locations:
            self.setdefault(result.rule_id, {}).setdefault(loc.file, []).append(result)

    def store_tool_data(self, tool_data: dict):
        if tool_data:
            self.tools.append(tool_data)

    def results_for_rule_and_file(
        self, context: CodemodExecutionContext, rule_id: str, file: Path
    ) -> list[ResultType]:
        """
        Return list of results for a given rule and file.

        :param context: The codemod execution context
        :param rule_id: The rule ID
        :param file: The filename

        Some implementers may need to use the context to compute paths that are relative to the target directory.
        """
        return self.get(rule_id, {}).get(file.relative_to(context.directory), [])

    def results_for_rules(self, rule_ids: list[str]) -> list[ResultType]:
        """
        Returns flat list of all results that match any of the given rule IDs.
        """
        return list(
            itertools.chain.from_iterable(
                self.results_for_rule.get(rule_id, []) for rule_id in rule_ids
            )
        )

    def result_by_finding_id(self, finding_id: str) -> ResultType | None:
        """Returns first result matching the given finding ID."""
        return next(
            (
                result
                for results in self.results_for_rule.values()
                for result in results
                if result.finding and result.finding.id == finding_id
            ),
            None,
        )

    def files_for_rule(self, rule_id: str) -> list[Path]:
        return list(self.get(rule_id, {}).keys())

    def all_rule_ids(self) -> list[str]:
        return list(self.keys())

    @classmethod
    def from_single_result(cls, result: ResultType) -> Self:
        """
        Creates a new ResultSet of the same type with a give result.
        """
        new = cls()
        new.add_result(result)
        return new

    def __or__(self, other):
        result = self.__class__()
        for k in self.keys() | other.keys():
            result[k] = list_dict_or(self.get(k, {}), other.get(k, {}))
        result.results_for_rule = list_dict_or(
            self.results_for_rule, other.results_for_rule
        )
        for tool in self.tools or other.tools:
            result.store_tool_data(tool)

        return result

    def __ior__(self, other):
        return self | other


def list_dict_or(
    dictionary: dict[Any, list[Any]], other: dict[Any, list[Any]]
) -> dict[Any, list[Any]]:
    result_dict = {}
    for k in other.keys() | dictionary.keys():
        result_dict[k] = list(
            IndexedSet(dictionary.get(k, [])) | (IndexedSet(other.get(k, [])))
        )
    return result_dict
