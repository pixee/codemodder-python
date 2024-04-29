import itertools
import json
import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Iterable, Optional

from typing_extensions import Self, override

from codemodder.context import CodemodExecutionContext
from codemodder.logging import logger
from codemodder.result import LineInfo, Location, Result, ResultSet
from codemodder.sarifs import AbstractSarifToolDetector


class SemgrepSarifToolDetector(AbstractSarifToolDetector):
    @classmethod
    def detect(cls, run_data: dict) -> bool:
        return (
            "tool" in run_data
            and "semgrep" in run_data["tool"]["driver"]["name"].lower()
        )


class SemgrepLocation(Location):
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


class SemgrepResult(Result):
    @classmethod
    def extract_rule_id(
        cls, result, sarif_run, truncate_rule_id: bool = False
    ) -> Optional[str]:
        if rule_id := result.get("ruleId"):
            return rule_id.split(".")[-1] if truncate_rule_id else rule_id

        # it may be contained in the 'rule' field through the tool component in the sarif file
        if "rule" in result:
            tool_index = result["rule"]["toolComponent"]["index"]
            rule_index = result["rule"]["index"]
            return sarif_run["tool"]["extensions"][tool_index]["rules"][rule_index][
                "id"
            ]

        return None

    @classmethod
    def from_sarif(
        cls, sarif_result, sarif_run, truncate_rule_id: bool = False
    ) -> Self:
        if not (rule_id := cls.extract_rule_id(sarif_result, sarif_run, truncate_rule_id)):
            raise ValueError("Could not extract rule id from sarif result.")

        locations: list[Location] = []
        for location in sarif_result["locations"]:
            artifact_location = SemgrepLocation.from_sarif(location)
            locations.append(artifact_location)
        return cls(rule_id=rule_id, locations=locations)


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
            raise subprocess.CalledProcessError(call.returncode, command)
        # semgrep prepends the folders into the rule-id, we want the base name only
        results = InternalSemgrepResultSet.from_sarif(
            temp_sarif_file.name, truncate_rule_id=True
        )
        return results
