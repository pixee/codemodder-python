from collections import defaultdict
import json
from pathlib import Path
from typing import List, Union


def extract_rule_id(result, sarif_run) -> Union[str, None]:
    if "ruleId" in result:
        # semgrep preprends the folders into the rule-id, we want the base name only
        return result["ruleId"].rsplit(".")[-1]

    # it may be contained in the 'rule' field through the tool component in the sarif file
    if "rule" in result:
        tool_index = result["rule"]["toolComponent"]["index"]
        rule_index = result["rule"]["index"]
        return sarif_run["tool"]["extensions"][tool_index]["rules"][rule_index]["id"]

    return None


def results_by_path_and_rule_id(sarif_file):
    """
    Extract all the results of a sarif file and organize them by id.
    """
    with open(sarif_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    path_and_ruleid_dict = defaultdict(lambda: defaultdict(list))
    for sarif_run in data["runs"]:
        results = sarif_run["results"]

        path_dict = defaultdict(list)
        for r in results:
            path = r["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]
            path_dict.setdefault(path, []).append(r)

        for path in path_dict.keys():
            rule_id_dict = defaultdict(list)
            for r in path_dict.get(path):
                # semgrep preprends the folders into the rule-id, we want the base name only
                rule_id = extract_rule_id(r, sarif_run)
                if rule_id:
                    rule_id_dict.setdefault(rule_id, []).append(r)
            path_and_ruleid_dict[path].update(rule_id_dict)
    return path_and_ruleid_dict


def parse_sarif_files(sarifs: List[Path]) -> defaultdict[str, defaultdict[str, List]]:
    """
    Parse sarif files organize their results into a dict of dicts organized by path and id.
    """
    path_id_dict: defaultdict[str, defaultdict[str, List]] = defaultdict(
        lambda: defaultdict(list)
    )
    for path in sarifs:
        path_id_dict.update(results_by_path_and_rule_id(Path(path)))
    return path_id_dict
