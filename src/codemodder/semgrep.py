import subprocess
import itertools
import yaml
from importlib.resources import files
from tempfile import NamedTemporaryFile
from typing import List
from pathlib import Path
from codemodder.context import CodemodExecutionContext
from codemodder.sarifs import results_by_path_and_rule_id
from codemodder.logging import logger

YAML_FILES_PACKAGE = "codemodder.codemods.semgrep"


def run_on_directory(yaml_files: List[Path], directory: Path):
    """
    Runs Semgrep and outputs a dict with the results organized by rule_id.
    """
    with NamedTemporaryFile(prefix="semgrep", suffix=".sarif") as temp_sarif_file:
        command = [
            "semgrep",
            "scan",
            "--legacy",
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
        results = results_by_path_and_rule_id(temp_sarif_file.name)
        return results


def run(execution_context: CodemodExecutionContext, codemods: dict) -> dict:
    semgrep_codemods = only_semgrep(codemods)
    if semgrep_codemods:
        return run_on_directory(
            find_all_yaml_files(semgrep_codemods), execution_context.directory
        )
    return {}


def find_all_yaml_files(codemods) -> list[Path]:
    """
    Finds all yaml files associated with the given codemods.
    """
    return [
        files(YAML_FILES_PACKAGE) / yaml_file
        for codemod in codemods.values()
        for yaml_file in codemod.YAML_FILES
    ]


def only_semgrep(codemods) -> dict:
    """
    Returns only semgrep codemods.
    """
    return {name: codemod for name, codemod in codemods.items() if codemod.IS_SEMGREP}


def rule_ids_from_yaml_files(yaml_files):
    all_yaml = []
    for file in yaml_files:
        with open(files(YAML_FILES_PACKAGE) / file, encoding="utf-8") as yaml_file:
            all_yaml.append(yaml.load(yaml_file, Loader=yaml.Loader))
    return [r["id"] for yaml_file in all_yaml for r in yaml_file["rules"]]
