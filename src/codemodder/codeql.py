import json
from pathlib import Path

from typing_extensions import Self

from codemodder.result import LineInfo, Location, Result, ResultSet
from codemodder.sarifs import AbstractSarifToolDetector


class CodeQLSarifToolDetector(AbstractSarifToolDetector):
    @classmethod
    def detect(cls, run_data: dict) -> bool:
        return "tool" in run_data and "CodeQL" in run_data["tool"]["driver"]["name"]


class CodeQLLocation(Location):
    @classmethod
    def from_sarif(cls, sarif_location) -> Self:
        artifact_location = sarif_location["physicalLocation"]["artifactLocation"]
        file = Path(artifact_location["uri"])

        try:
            region = sarif_location["physicalLocation"]["region"]
        except KeyError:
            # A location without a region indicates a result for the entire file.
            # Use sentinel values of 0 index for start/end
            zero = LineInfo(0)
            return cls(file=file, start=zero, end=zero)

        start = LineInfo(line=region["startLine"], column=region.get("startColumn"))
        end = LineInfo(
            line=region.get("endLine", start.line),
            column=region.get("endColumn", start.column),
        )
        return cls(file=file, start=start, end=end)


class CodeQLResult(Result):
    @classmethod
    def from_sarif(
        cls, sarif_result, sarif_run, rule_extensions, truncate_rule_id: bool = False
    ) -> Self:
        extension_index = sarif_result["rule"]["toolComponent"]["index"]
        tool_index = sarif_result["rule"]["index"]
        rule_data = rule_extensions[extension_index]["rules"][tool_index]

        locations: list[Location] = []
        for location in sarif_result["locations"]:
            try:
                codeql_location = CodeQLLocation.from_sarif(location)
            except KeyError:
                continue

            locations.append(codeql_location)
        return cls(rule_id=rule_data["id"], locations=locations)


class CodeQLResultSet(ResultSet):
    @classmethod
    def from_sarif(cls, sarif_file: str | Path, truncate_rule_id: bool = False) -> Self:
        with open(sarif_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        result_set = cls()
        for sarif_run in data["runs"]:
            rule_extensions = sarif_run["tool"]["extensions"]
            if CodeQLSarifToolDetector.detect(sarif_run):
                for sarif_result in sarif_run["results"]:
                    codeql_result = CodeQLResult.from_sarif(
                        sarif_result, sarif_run, rule_extensions, truncate_rule_id
                    )
                    result_set.add_result(codeql_result)
        return result_set
