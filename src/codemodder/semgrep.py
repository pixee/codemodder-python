import subprocess
import itertools
from tempfile import NamedTemporaryFile
from typing import List
from pathlib import Path
from codemodder.context import CodemodExecutionContext
from codemodder.sarifs import results_by_path_and_rule_id
from codemodder.logging import logger


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
    return list(itertools.chain(*[codemod.yaml_files for codemod in codemods.values()]))


def only_semgrep(codemods) -> dict:
    """
    Returns only semgrep codemods.
    """
    return {name: codemod for name, codemod in codemods.items() if codemod.is_semgrep}
