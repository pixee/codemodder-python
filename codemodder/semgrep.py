import json
import subprocess
import itertools
import yaml
from tempfile import NamedTemporaryFile
from typing import List
from pathlib import Path
from collections import defaultdict
from codemodder import global_state
from codemodder.logging import logger

YAML_FILES_DIR = Path("codemodder") / "codemods" / "semgrep"


def run_on_directory(yaml_files: List[Path], directory: Path):
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
        command.append(str(directory))
        joined_command = " ".join(command)
        logger.debug("Executing semgrep with: `%s`", joined_command)
        subprocess.run(joined_command, shell=True, check=True)
        results = results_by_path_and_rule_id(temp_sarif_file)
        return results


def run(yaml_files: List[Path]):
    return run_on_directory(yaml_files, Path(global_state.DIRECTORY))


def find_all_yaml_files(codemods) -> list[Path]:
    """
    Finds all yaml files associated with the given codemods.
    """
    return [
        YAML_FILES_DIR / yaml_file
        for codemod in codemods.values()
        for yaml_file in codemod.YAML_FILES
    ]


def results_by_path_and_rule_id(sarif_file):
    """
    Extract all the results of a sarif file and organize them by id.
    """
    # TODO ruleId could be indirectly pointed by the rule field
    # TODO test with webgoat sarif
    with open(sarif_file.name, "r", encoding="utf-8") as f:
        data = json.load(f)
    results = [result for sarif_run in data["runs"] for result in sarif_run["results"]]

    path_dict = defaultdict(list)
    for r in results:
        path = r["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]
        path_dict.setdefault(path, []).append(r)

    path_and_ruleid_dict = defaultdict(lambda: defaultdict(list))
    for path in path_dict.keys():
        rule_id_dict = defaultdict(list)
        for r in path_dict.get(path):
            # semgrep preprends the folders into the rule-id, we want the base name only
            rule_id = r["ruleId"].rsplit(".")[-1]
            rule_id_dict.setdefault(rule_id, []).append(r)
        path_and_ruleid_dict[path] = rule_id_dict
    return path_and_ruleid_dict


def rule_ids_from_yaml_files(yaml_files):
    all_yaml = []
    for file in yaml_files:
        with open(YAML_FILES_DIR / file, encoding="utf-8") as yaml_file:
            all_yaml.append(yaml.load(yaml_file, Loader=yaml.Loader))
    return [r["id"] for yaml_file in all_yaml for r in yaml_file["rules"]]
