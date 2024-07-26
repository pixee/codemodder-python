import json
from pathlib import Path

from typing_extensions import Self

from codemodder.codetf import Finding, Rule
from codemodder.result import LineInfo, ResultSet, SarifLocation, SarifResult
from codemodder.sarifs import AbstractSarifToolDetector


class CodeQLSarifToolDetector(AbstractSarifToolDetector):
    @classmethod
    def detect(cls, run_data: dict) -> bool:
        return "tool" in run_data and "CodeQL" in run_data["tool"]["driver"]["name"]


class CodeQLLocation(SarifLocation):
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


class CodeQLResult(SarifResult):
    location_type = CodeQLLocation

    @classmethod
    def from_sarif(
        cls, sarif_result, sarif_run, truncate_rule_id: bool = False
    ) -> Self:
        return cls(
            rule_id=(
                rule_id := cls.extract_rule_id(
                    sarif_result, sarif_run, truncate_rule_id
                )
            ),
            locations=cls.extract_locations(sarif_result),
            codeflows=cls.extract_code_flows(sarif_result),
            related_locations=cls.extract_related_locations(sarif_result),
            finding_id=rule_id,
            finding=Finding(
                id=rule_id,
                rule=Rule(
                    id=rule_id,
                    name=rule_id,
                    # TODO: map to URL
                    # url=,
                ),
            ),
        )


class CodeQLResultSet(ResultSet):
    @classmethod
    def from_sarif(cls, sarif_file: str | Path, truncate_rule_id: bool = False) -> Self:
        with open(sarif_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        result_set = cls()
        for sarif_run in data["runs"]:
            if CodeQLSarifToolDetector.detect(sarif_run):
                for sarif_result in sarif_run["results"]:
                    codeql_result = CodeQLResult.from_sarif(
                        sarif_result, sarif_run, truncate_rule_id
                    )
                    result_set.add_result(codeql_result)
        return result_set
