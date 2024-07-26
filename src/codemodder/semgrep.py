import itertools
import json
import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Iterable, Optional

from typing_extensions import Self, override

from codemodder.codetf import Finding, Rule
from codemodder.context import CodemodExecutionContext
from codemodder.logging import logger
from codemodder.result import LineInfo, Result, ResultSet, SarifLocation, SarifResult
from codemodder.sarifs import AbstractSarifToolDetector


class SemgrepSarifToolDetector(AbstractSarifToolDetector):
    @classmethod
    def detect(cls, run_data: dict) -> bool:
        return (
            "tool" in run_data
            and "semgrep" in run_data["tool"]["driver"]["name"].lower()
        )


class SemgrepLocation(SarifLocation):
    @classmethod
    def from_sarif(cls, sarif_location) -> Self:
        artifact_location = sarif_location["physicalLocation"]["artifactLocation"]
        file = Path(artifact_location["uri"])
        start = LineInfo(
            line=sarif_location["physicalLocation"]["region"]["startLine"],
            column=sarif_location["physicalLocation"]["region"]["startColumn"],
            snippet=sarif_location["physicalLocation"]["region"]["snippet"]["text"],
        )
        end = LineInfo(
            line=sarif_location["physicalLocation"]["region"]["endLine"],
            column=sarif_location["physicalLocation"]["region"]["endColumn"],
            snippet=sarif_location["physicalLocation"]["region"]["snippet"]["text"],
        )
        return cls(file=file, start=start, end=end)


class SemgrepResult(SarifResult):
    location_type = SemgrepLocation

    @classmethod
    def from_sarif(
        cls, sarif_result, sarif_run, truncate_rule_id: bool = False
    ) -> Self:
        # avoid circular import
        from core_codemods.semgrep.api import semgrep_url_from_id

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
                    url=semgrep_url_from_id(rule_id),
                ),
            ),
        )


class SemgrepResultSet(ResultSet):
    @classmethod
    def from_sarif(cls, sarif_file: str | Path, truncate_rule_id: bool = False) -> Self:
        with open(sarif_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        result_set = cls()
        for sarif_run in data["runs"]:
            for result in sarif_run["results"]:
                sarif_result = SemgrepResult.from_sarif(
                    result, sarif_run, truncate_rule_id
                )
                result_set.add_result(sarif_result)

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

    with NamedTemporaryFile(prefix="semgrep", suffix=".sarif") as temp_sarif_file:
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
