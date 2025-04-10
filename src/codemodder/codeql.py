from pathlib import Path

from sarif_pydantic import Location as LocationModel
from sarif_pydantic import Result as ResultModel
from sarif_pydantic import Sarif
from typing_extensions import Self

from codemodder.result import LineInfo, ResultSet, SarifLocation, SarifResult
from codemodder.sarifs import AbstractSarifToolDetector, Run


class CodeQLSarifToolDetector(AbstractSarifToolDetector):
    @classmethod
    def detect(cls, run_data: Run) -> bool:
        return "CodeQL" in run_data.tool.driver.name


class CodeQLLocation(SarifLocation):
    @classmethod
    def from_sarif(cls, run: Run, sarif_location: LocationModel) -> Self:
        del run
        if (physical_location := sarif_location.physical_location) is None:
            raise ValueError("Location does not contain a physicalLocation")
        if (artifact_location := physical_location.artifact_location) is None:
            raise ValueError("PhysicalLocation does not contain an artifactLocation")
        if (uri := artifact_location.uri) is None:
            raise ValueError("ArtifactLocation does not contain a uri")

        file = Path(uri)

        if not (region := physical_location.region):
            # A location without a region indicates a result for the entire file.
            # Use sentinel values of 0 index for start/end
            zero = LineInfo(0)
            return cls(file=file, start=zero, end=zero)

        if not region.start_line:
            raise ValueError("Region does not contain a startLine")

        start = LineInfo(line=region.start_line, column=region.start_column or -1)
        end = LineInfo(
            line=region.end_line or start.line,
            column=region.end_column or start.column,
        )
        return cls(file=file, start=start, end=end)


class CodeQLResult(SarifResult):
    location_type = CodeQLLocation

    @classmethod
    def rule_url_from_id(cls, result: ResultModel, run: Run, rule_id: str) -> str:
        del result, run, rule_id
        # TODO: Implement this method to return the specific rule URL
        return "https://codeql.github.com/codeql-query-help/"


class CodeQLResultSet(ResultSet):
    @classmethod
    def from_sarif(cls, sarif_file: str | Path, truncate_rule_id: bool = False) -> Self:
        data = Sarif.model_validate_json(
            Path(sarif_file).read_text(encoding="utf-8-sig")
        )

        result_set = cls()
        for sarif_run in data.runs:
            if CodeQLSarifToolDetector.detect(sarif_run):
                for sarif_result in sarif_run.results or []:
                    codeql_result = CodeQLResult.from_sarif(
                        sarif_result, sarif_run, truncate_rule_id
                    )
                    result_set.add_result(codeql_result)
                result_set.store_tool_data(sarif_run.tool.model_dump())
        return result_set
