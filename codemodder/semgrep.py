import json
import subprocess
import itertools
from tempfile import NamedTemporaryFile
from typing import List
from pathlib import Path
from collections import defaultdict
from codemodder.logging import logger


def run(project_root: Path, yaml_files: List[Path]):
    """
    Runs Semgrep and outputs a dict with the results organized by rule_id.
    """
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
        command.append(str(project_root))
        joined_command = " ".join(command)
        logger.debug("Executing semgrep with: `%s`", joined_command)
        subprocess.run(joined_command, shell=True, check=True)
        results = results_by_rule_id(temp_sarif_file)
        return results


def find_all_yaml_files(codemods) -> list[Path]:  # pylint: disable=unused-argument
    """
    Finds all yaml files associated with the given codemods.
    """
    # TODO for now, just pass everything until we figure out semgrep codemods
    return list((Path("codemodder") / "codemods" / "semgrep").iterdir())


def results_by_rule_id(sarif_file):
    """
    Extract all the results of a sarif file and organize them by id.
    """
    # TODO ruleId could be indirectly pointed by the rule field
    # TODO test with webgoat sarif
    with open(sarif_file.name, "r", encoding="utf-8") as f:
        data = json.load(f)
    results = [result for sarif_run in data["runs"] for result in sarif_run["results"]]
    rule_id_dict = defaultdict(list)
    for r in results:
        # semgrep preprends the folders into the rule-id, we want the base name only
        rule_id = r["ruleId"].rsplit(".")[-1]
        rule_id_dict.setdefault(rule_id, []).append(r)
    return rule_id_dict


def get_results():
    """
    Extract the results of a semgrep run.
    """
    with open("sarif.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    return data["runs"][0]["results"]
