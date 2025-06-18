import json
from dataclasses import replace
from functools import cache
from pathlib import Path
from typing import Sequence

import libcst as cst
from typing_extensions import Self

from codemodder.codetf import Finding, Rule
from codemodder.logging import logger
from codemodder.result import LineInfo, Location, ResultSet, SASTResult


def sonar_url_from_id(rule_id: str) -> str:
    language = "python"
    try:
        # convert "python:SXXX" or "pythonsecurity:SXXX" to python and XXX
        prefix, number = rule_id.split(":")
        number = number[1:]
        match prefix:
            case "python" | "pythonsecurity":
                language = "python"
            case "java" | "javasecurity":
                language = "java"
            case "javascript" | "jssecurity":
                language = "javascript"
            case "typescript" | "tssecurity":
                language = "typescript"
            case "roslyn.sonaranalyzer.security.cs" | "csharpsquid":
                language = "dotnet"
            case "phpsecurity":
                language = "php"
            case "xml":
                language = "xml"
            case _:
                logger.debug(f"Unknown language in sonar rule: {prefix}")

    except IndexError:
        logger.debug("Invalid sonar rule id: %s", rule_id)
        raise

    return f"https://rules.sonarsource.com/{language}/RSPEC-{number}/"


class SonarLocation(Location):
    @classmethod
    def from_json_location(cls, json_location) -> Self:
        location = json_location.get("textRange")
        start = LineInfo(location.get("startLine"), location.get("startOffset"), "")
        end = LineInfo(location.get("endLine"), location.get("endOffset"), "")
        file = Path(json_location.get("component").split(":")[-1])
        return cls(file=file, start=start, end=end)


class SonarResult(SASTResult):

    @classmethod
    def from_result(cls, result: dict) -> Self:
        # Sonar issues have `rule` as key while hotspots call it `ruleKey`
        if not (rule_id := result.get("rule", None) or result.get("ruleKey", None)):
            raise ValueError("Could not extract rule id from sarif result.")

        locations: Sequence[Location] = tuple(
            [SonarLocation.from_json_location(result)]
            if result.get("textRange")
            else []
        )
        all_flows: Sequence[Sequence[Location]] = tuple(
            [
                tuple(
                    [
                        SonarLocation.from_json_location(json_location)
                        for json_location in flow.get("locations", {})
                    ]
                )
                for flow in result.get("flows", [])
            ]
        )

        finding_id = result.get("key", rule_id)

        # Both issues and hotspots have a `message` key
        name = result.get("message", None) or rule_id

        return cls(
            finding_id=finding_id,
            rule_id=rule_id,
            locations=locations,
            codeflows=all_flows,
            finding=Finding(
                id=finding_id,
                rule=Rule(
                    id=rule_id,
                    name=name,
                    url=sonar_url_from_id(rule_id),
                ),
            ),
        )

    def match_location(self, pos, node):
        match node:
            case cst.Tuple():
                new_pos = replace(
                    pos,
                    start=replace(pos.start, column=pos.start.column - 1),
                    end=replace(pos.end, column=pos.end.column + 1),
                )
                return super().match_location(new_pos, node)
        return super().match_location(pos, node)


class SonarResultSet(ResultSet):
    @classmethod
    @cache
    def from_json(cls, json_file: str | Path) -> Self:
        try:
            with open(json_file, "r", encoding="utf-8") as file:
                data = json.load(file)

            result_set = cls()
            for result in data.get("issues", []) + data.get("hotspots", []):
                result_set.add_result(SonarResult.from_result(result))

            return result_set
        except Exception:
            logger.exception("Could not parse sonar json %s", json_file)
        return cls()
