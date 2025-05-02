import itertools
import json
import subprocess
import uuid
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Iterable, Optional

from sarif_pydantic import Sarif
from typing_extensions import Self, override

from codemodder.context import CodemodExecutionContext
from codemodder.logging import logger
from codemodder.result import (
    LocationModel,
    Result,
    ResultModel,
    ResultSet,
    SarifLocation,
    SarifResult,
)
from codemodder.sarifs import AbstractSarifToolDetector, Run


class SemgrepSarifToolDetector(AbstractSarifToolDetector):
    @classmethod
    def detect(cls, run_data: Run) -> bool:
        return "semgrep" in run_data.tool.driver.name.lower()


class SemgrepLocation(SarifLocation):
    @staticmethod
    def get_snippet(sarif_location: LocationModel) -> str | None:
        return (
            sarif_location.physical_location.region.snippet.text
            if sarif_location.physical_location
            and sarif_location.physical_location.region
            and sarif_location.physical_location.region.snippet
            else SarifLocation.get_snippet(sarif_location)
        )


class SemgrepResult(SarifResult):
    location_type = SemgrepLocation

    @override
    @classmethod
    def rule_url_from_id(
        cls, result: ResultModel, run: Run, rule_id: str
    ) -> str | None:
        del result, run
        from core_codemods.semgrep.api import semgrep_url_from_id

        return semgrep_url_from_id(rule_id)


class SemgrepResultSet(ResultSet):
    @classmethod
    def from_sarif(cls, sarif_file: str | Path, truncate_rule_id: bool = False) -> Self:
        data = Sarif.model_validate_json(Path(sarif_file).read_text())

        result_set = cls()
        for sarif_run in data.runs:
            for result in sarif_run.results or []:
                sarif_result = SemgrepResult.from_sarif(
                    result, sarif_run, truncate_rule_id
                )
                result_set.add_result(sarif_result)
            result_set.store_tool_data(sarif_run.tool.model_dump())
        return result_set


class InternalSemgrepResultSet(SemgrepResultSet):
    @override
    def results_for_rule_and_file(
        self, context: CodemodExecutionContext, rule_id: str, file: Path
    ) -> list[Result]:
        del context
        paths_for_rule = self.get(rule_id, {})
        # Do not normalize the path
        return paths_for_rule.get(file, [])


def run(
    execution_context: CodemodExecutionContext,
    yaml_files: Iterable[Path],
    files_to_analyze: Optional[Iterable[Path]] = None,
) -> SemgrepResultSet:
    """
    Runs Semgrep and outputs a dict with the results organized by rule_id.
    """
    if not yaml_files:
        raise ValueError("No Semgrep rules were provided")

    with NamedTemporaryFile(
        prefix="semgrep", suffix=".sarif", mode="w+"
    ) as temp_sarif_file:
        command = [
            "semgrep",
            "scan",
            "--no-error",
            "--dataflow-traces",
            "--sarif",
            "-o",
            temp_sarif_file.name,
        ]
        command.extend(
            itertools.chain.from_iterable(
                map(lambda f: ["--config", str(f)], yaml_files)
            )
        )
        command.extend(map(str, files_to_analyze or [execution_context.directory]))
        logger.debug("semgrep command: `%s`", " ".join(command))
        call = subprocess.run(
            command,
            shell=False,
            check=False,
            stdout=None if execution_context.verbose else subprocess.PIPE,
            stderr=None if execution_context.verbose else subprocess.PIPE,
        )
        # Insert guid in results
        temp_sarif_file.seek(0)
        sarif = Sarif.model_validate(json.load(temp_sarif_file))
        for run in sarif.runs:
            for result in run.results or []:
                if not result.guid:
                    result.guid = uuid.uuid4()
        temp_sarif_file.seek(0)
        temp_sarif_file.write(sarif.model_dump_json(exclude_none=True, by_alias=True))
        temp_sarif_file.seek(0)

        if call.returncode != 0:
            if not execution_context.verbose:
                logger.error("captured semgrep stderr: %s", call.stderr)
            try:
                logger.error("semgrep sarif output: %s", temp_sarif_file.read())
            except Exception as e:
                logger.error("failed to read semgrep sarif output: %s", e)

            raise subprocess.CalledProcessError(call.returncode, command)
        # semgrep prepends the folders into the rule-id, we want the base name only
        results = InternalSemgrepResultSet.from_sarif(
            temp_sarif_file.name, truncate_rule_id=True
        )
        return results
