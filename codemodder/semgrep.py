import subprocess
import itertools
import yaml
from tempfile import NamedTemporaryFile
from typing import List
from pathlib import Path
from codemodder import global_state
from codemodder.sarifs import results_by_path_and_rule_id
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


def rule_ids_from_yaml_files(yaml_files):
    all_yaml = []
    for file in yaml_files:
        with open(YAML_FILES_DIR / file, encoding="utf-8") as yaml_file:
            all_yaml.append(yaml.load(yaml_file, Loader=yaml.Loader))
    return [r["id"] for yaml_file in all_yaml for r in yaml_file["rules"]]
