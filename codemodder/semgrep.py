import json
import subprocess
from tempfile import NamedTemporaryFile
from typing import List
from pathlib import Path


def run(project_root: Path, yaml_files: List[Path]):
    """
    Runs Semgrep and outputs the result in a Sarif TemporaryFile.
    """
    # TODO Look into running semgrep from its module later
    temp_sarif_file = NamedTemporaryFile(prefix="semgrep", suffix=".sarif")
    command = [
        "semgrep",
        "scan",
        "--no-error",
        "--dataflow-traces",
        "--sarif",
        "-o",
        temp_sarif_file.name,
    ]
    command += list(map(lambda f: "--config " + str(f), yaml_files))
    command += [str(project_root)]
    print(f"Executing semgrep with: {command}")
    subprocess.run(" ".join(command), shell=True, check=True)
    return temp_sarif_file


def find_all_yaml_files(codemods) -> list[Path]:
    """
    Finds all yaml files associated with the given codemods.
    """
    # TODO for now, just pass everything until we figure out semgrep codemods
    return list((Path("codemodder") / "codemods" / "semgrep").iterdir())


def results_by_id(sarif_file):
    """
    Extract all the results of a sarif file and organize them by id.
    """


def get_results():
    """
    Extract the results of a semgrep run.
    """
    with open("sarif.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    return data["runs"][0]["results"]
