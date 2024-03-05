import json
from abc import ABCMeta, abstractmethod
from importlib.metadata import entry_points
from pathlib import Path
from typing import Optional

from typing_extensions import Self

from codemodder.logging import logger

from .result import LineInfo, Location, Result, ResultSet


class AbstractSarifToolDetector(metaclass=ABCMeta):
    @classmethod
    @abstractmethod
    def detect(cls, run_data: dict) -> bool:
        pass


def detect_sarif_tools(filenames: list[Path]) -> dict[str, list[str]]:
    results: dict[str, list[str]] = {}

    logger.debug("loading registered SARIF tool detectors")
    detectors = {
        ent.name: ent.load() for ent in entry_points().select(group="sarif_detectors")
    }
    for fname in filenames:
        data = json.loads(fname.read_text())
        for name, det in detectors.items():
            # TODO: handle malformed sarif?
            for run in data["runs"]:
                try:
                    if det.detect(run):
                        logger.debug("detected %s sarif: %s", name, fname)
                        results.setdefault(name, []).append(str(fname))
                except (KeyError, AttributeError, ValueError):
                    continue

    return results


def extract_rule_id(result, sarif_run) -> Optional[str]:
    if "ruleId" in result:
        # semgrep preprends the folders into the rule-id, we want the base name only
        return result["ruleId"].rsplit(".")[-1]

    # it may be contained in the 'rule' field through the tool component in the sarif file
    if "rule" in result:
        tool_index = result["rule"]["toolComponent"]["index"]
        rule_index = result["rule"]["index"]
        return sarif_run["tool"]["extensions"][tool_index]["rules"][rule_index]["id"]

    return None


# NOTE: These Sarif classes are actually specific to Semgrep and should be moved elsewhere
class SarifLocation(Location):
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


class SarifResult(Result):
    @classmethod
    def from_sarif(cls, sarif_result, sarif_run) -> Self:
        rule_id = extract_rule_id(sarif_result, sarif_run)
        if not rule_id:
            raise ValueError("Could not extract rule id from sarif result.")

        locations: list[Location] = []
        for location in sarif_result["locations"]:
            artifact_location = SarifLocation.from_sarif(location)
            locations.append(artifact_location)
        return cls(rule_id=rule_id, locations=locations)


class SarifResultSet(ResultSet):
    @classmethod
    def from_sarif(cls, sarif_file: str | Path) -> Self:
        with open(sarif_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        result_set = cls()
        for sarif_run in data["runs"]:
            for result in sarif_run["results"]:
                sarif_result = SarifResult.from_sarif(result, sarif_run)
                result_set.add_result(sarif_result)

        return result_set
