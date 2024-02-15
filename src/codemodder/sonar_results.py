import libcst as cst
import json
from pathlib import Path
from typing_extensions import Self

from codemodder.result import LineInfo, Location, Result, ResultSet
from codemodder.logging import logger
from dataclasses import replace


class SonarLocation(Location):
    @classmethod
    def from_issue(cls, issue) -> Self:
        location = issue.get("textRange")
        start = LineInfo(location.get("startLine"), location.get("startOffset"), "")
        end = LineInfo(location.get("endLine"), location.get("endOffset"), "")
        file = Path(issue.get("component").split(":")[-1])
        return cls(file=file, start=start, end=end)


class SonarResult(Result):

    @classmethod
    def from_issue(cls, issue) -> Self:
        rule_id = issue.get("rule", None)
        if not rule_id:
            raise ValueError("Could not extract rule id from sarif result.")

        locations: list[Location] = [SonarLocation.from_issue(issue)]
        return cls(rule_id=rule_id, locations=locations)

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
    def from_json(cls, json_file: str | Path) -> Self:
        try:
            with open(json_file, "r", encoding="utf-8") as file:
                data = json.load(file)

            result_set = cls()
            for issue in data.get("issues"):
                if issue["status"].lower() == "open":
                    result_set.add_result(SonarResult.from_issue(issue))

            return result_set
        except Exception:
            logger.debug("Could not parse sonar json %s", json_file)
        return cls()
