import json
from dataclasses import replace
from functools import cache
from pathlib import Path

import libcst as cst
from typing_extensions import Self

from codemodder.codetf import Finding, Rule
from codemodder.logging import logger
from codemodder.result import LineInfo, Location, ResultSet, SASTResult


def sonar_url_from_id(rule_id: str) -> str:
    # convert "python:SXXX" or "pythonsecurity:SXXX" to XXX
    try:
        rule_id = rule_id.split(":")[1][1:]
    except IndexError:
        logger.debug("Invalid sonar rule id: %s", rule_id)
        raise

    return f"https://rules.sonarsource.com/python/RSPEC-{rule_id}/"


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

        locations: list[Location] = [SonarLocation.from_json_location(result)]
        all_flows: list[list[Location]] = [
            [
                SonarLocation.from_json_location(json_location)
                for json_location in flow.get("locations", {})
            ]
            for flow in result.get("flows", [])
        ]

        return cls(
            finding_id=rule_id,
            rule_id=rule_id,
            locations=locations,
            codeflows=all_flows,
            finding=Finding(
                id=rule_id,
                rule=Rule(
                    id=rule_id,
                    name=rule_id,
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
            for result in data.get("issues") or [] + data.get("hotspots") or []:
                if result["status"].lower() in ("open", "to_review"):
                    result_set.add_result(SonarResult.from_result(result))

            return result_set
        except Exception:
            logger.exception("Could not parse sonar json %s", json_file)
        return cls()
